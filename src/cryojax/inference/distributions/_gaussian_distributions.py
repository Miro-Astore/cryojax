"""
Image formation models simulated from gaussian distributions.
"""

from typing import Optional, Any
from typing_extensions import override

import equinox as eqx
import jax.random as jr
import jax.numpy as jnp
from jaxtyping import PRNGKeyArray

from ._distribution import AbstractDistribution
from ...image.operators import FourierOperatorLike, Constant
from ...simulator import GaussianIce
from ...simulator import GaussianDetector
from ...simulator import AbstractPipeline
from ...typing import Real_, RealImage, ComplexImage


class IndependentFourierGaussian(AbstractDistribution, strict=True):
    r"""
    A gaussian noise model, where each fourier mode is independent.

    This computes the likelihood in Fourier space,
    which allows one to model an arbitrary noise power spectrum.

    If no variance model is explicitly passed, the variance is computed as

    .. math::
        Var[D(q)] + CTF(q)^2 Var[I(q)]

    where :math:`D(q)` and :math:`I(q)` are independent gaussian random variables in fourier
    space for the detector and ice, respectively, for a given fourier mode :math:`q`.

    Attributes
    ----------
    variance :
        The gaussian variance function. If not given, use the detector and ice noise
        models as described above.
    """

    pipeline: AbstractPipeline
    variance: FourierOperatorLike

    def __init__(
        self,
        pipeline: AbstractPipeline,
        variance: Optional[FourierOperatorLike] = None,
    ):
        self.pipeline = pipeline
        if variance is None:
            # Variance from detector
            if isinstance(pipeline.instrument.detector, GaussianDetector):
                variance = pipeline.instrument.detector.variance
            else:
                variance = Constant(0.0)
            # Variance from ice
            if isinstance(pipeline.solvent, GaussianIce):
                ctf = pipeline.instrument.optics.ctf
                variance += ctf * ctf * pipeline.solvent.variance
            if eqx.tree_equal(variance, Constant(0.0)):
                raise AttributeError(
                    "If variance is not given, the ImagePipeline must have either a GaussianDetector or GaussianIce model."
                )
        self.variance = variance

    @override
    def sample(self, key: PRNGKeyArray, **kwargs: Any) -> RealImage:
        """Sample from the Gaussian noise model."""
        freqs = self.pipeline.scattering.config.padded_frequency_grid_in_angstroms.get()
        noise = self.variance(freqs) * jr.normal(key, shape=freqs.shape[0:-1])
        image = self.pipeline.render(view_cropped=False, get_real=False)
        return self.pipeline.crop_and_apply_operators(image + noise, **kwargs)

    @override
    def log_probability(self, observed: ComplexImage) -> Real_:
        """Evaluate the log-likelihood of the gaussian noise model.

        **Arguments:**

        `observed` : The observed data in fourier space. `observed.shape`
                     must match `ImageConfig.padded_shape`.
        """
        pipeline = self.pipeline
        padded_freqs = (
            pipeline.scattering.config.padded_frequency_grid_in_angstroms.get()
        )
        freqs = pipeline.scattering.config.frequency_grid_in_angstroms.get()
        if observed.shape != padded_freqs.shape[:-1]:
            raise ValueError("Shape of observed must match ImageConfig.padded_shape")
        # Get residuals
        residuals = pipeline.render(view_cropped=False, get_real=False) - observed
        # Apply filters, crop, and mask
        residuals = pipeline.crop_and_apply_operators(residuals, get_real=False)
        # Compute loss
        loss = jnp.sum(
            (residuals * jnp.conjugate(residuals)) / (2 * self.variance(freqs))
        )
        # Divide by number of modes (parseval's theorem)
        loss = loss.real / residuals.size

        return loss
