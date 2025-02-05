"""
Scattering methods using non-uniform FFTs.
"""

import math
from typing import Any, Union
from equinox import field

import jax.numpy as jnp

from .._config import ImageConfig
from .._density import RealVoxelCloud, RealVoxelGrid
from ._scattering_method import AbstractProjectionMethod
from ...typing import (
    ComplexImage,
    RealCloud,
    CloudCoords2D,
    CloudCoords3D,
)


class NufftProject(AbstractProjectionMethod, strict=True):
    """
    Scatter points to image plane using a
    non-uniform FFT.

    Attributes
    ----------
    eps : `float`
        See ``jax-finufft`` for documentation.
    """

    config: ImageConfig

    eps: float = field(static=True, default=1e-6)

    def project_density(self, density: RealVoxelGrid | RealVoxelCloud) -> ComplexImage:
        """Rasterize image with non-uniform FFTs."""
        if isinstance(density, RealVoxelGrid):
            shape = density.shape
            fourier_projection = project_with_nufft(
                density.density_grid.ravel(),
                density.coordinate_grid.get().reshape((math.prod(shape), 3)),
                self.config.padded_shape,
                eps=self.eps,
            )
        elif isinstance(density, RealVoxelCloud):
            fourier_projection = project_with_nufft(
                density.density_weights,
                density.coordinate_list.get(),
                self.config.padded_shape,
                eps=self.eps,
            )
        else:
            raise ValueError(
                "Supported density representations are RealVoxelGrid and VoxelCloud."
            )
        return fourier_projection


def project_with_nufft(
    weights: RealCloud,
    coordinate_list: Union[CloudCoords2D, CloudCoords3D],
    shape: tuple[int, int],
    eps: float = 1e-6,
) -> ComplexImage:
    """
    Project and interpolate 3D volume point cloud
    onto imaging plane using a non-uniform FFT.

    Arguments
    ---------
    weights : shape `(N,)`
        Density point cloud.
    coordinates : shape `(N, 2)` or shape `(N, 3)`
        Coordinate system of point cloud.
    shape :
        Shape of the imaging plane in pixels.
        ``width, height = shape[0], shape[1]``
        is the size of the desired imaging plane.

    Returns
    -------
    projection :
        The output image in fourier space.
    """
    from jax_finufft import nufft1

    weights, coordinate_list = jnp.asarray(weights).astype(complex), jnp.asarray(
        coordinate_list
    )
    # Get x and y coordinates
    coordinates_xy = coordinate_list[:, :2]
    # Normalize coordinates betweeen -pi and pi
    M1, M2 = shape
    image_size = jnp.asarray((M1, M2), dtype=float)
    coordinates_periodic = 2 * jnp.pi * coordinates_xy / image_size
    # Unpack and compute
    x, y = coordinates_periodic[:, 0], coordinates_periodic[:, 1]
    projection = nufft1(shape, weights, y, x, eps=eps, iflag=-1)
    # Shift zero frequency component to corner and take upper half plane
    projection = jnp.fft.ifftshift(projection)[:, : M2 // 2 + 1]
    # Set last line of frequencies to zero if image dimension is even
    if M2 % 2 == 0:
        projection = projection.at[:, -1].set(0.0 + 0.0j)
    if M1 % 2 == 0:
        projection = projection.at[M1 // 2, :].set(0.0 + 0.0j)
    return projection


"""
def project_atoms_with_nufft(
    weights,
    coordinates,
    variances,
    identity,
    shape: tuple[int, int],
    **kwargs: Any,
) -> ComplexImage:
    atom_types = jnp.unique(identity)
    img = jnp.zeros(shape, dtype=complex)
    for atom_type_i in atom_types:
        # Select the properties specific to that type of atom
        coords_i = coordinates[identity == atom_type_i]
        weights_i = weights[identity == atom_type_i]
        # kernel_i = atom_density_kernel[atom_type_i]

        # Build an
        atom_i_image = project_with_nufft(weights_i, coords_i, shape, **kwargs)

        # img += atom_i_image * kernel_i
        img += atom_i_image

    return img

class IndependentAtomScatteringNufft(NufftScattering):
    '''
    Projects a pointcloud of atoms onto the imaging plane.
    In contrast to the work in project_with_nufft, here each atom is

    TODO: Typehints for atom_density_kernel
    '''

    def scatter(
        self,
        density: RealCloud,
        coordinates: CloudCoords,
        pixel_size: float,
        identity: IntCloud,
        atom_density_kernel,  # WHAT SHOULD THE TYPE BE HERE?
    ) -> ComplexImage:
        '''
        Projects a pointcloud of atoms onto the imaging plane.
        In contrast to the work in project_with_nufft, here each atom is

        TODO: Typehints for atom_density_kernel
        '''
        atom_types = jnp.unique(identity)

        img = jnp.zeros(self.padded_shape, dtype=jnp.complex64)
        for atom_type_i in atom_types:
            # Select the properties specific to that type of atom
            coords_i = coordinates[identity == atom_type_i]
            density_i = density[identity == atom_type_i]
            kernel_i = atom_density_kernel[atom_type_i]

            # Build an
            atom_i_image = project_with_nufft(
                density_i,
                coords_i,
                pixel_size,
                self.padded_shape,
                # atom_density_kernel[atom_type_i],
            )

            # img += atom_i_image * kernel_i
            img += atom_i_image
        return img
"""
