#!/usr/bin/env python3
"""
Routines to model image formation
"""

import numpy as np
import jax.numpy as jnp
from functools import partial
from jax import jit
from interpolation import interpolate


@partial(jit, static_argnames=['shape'])
def project(volume, coords, shape):
    """
    Project 3D volume onto imaging plane.

    Parameters
    ----------
    volume : `jnp.ndarray`, shape `(N, 3)`
        3D volume.
    coords : `jnp.ndarray`, shape `(N, 3)`
        Coordinate system.
    shape : `tuple`
        A tuple denoting the shape of the output image, given
        by ``(N2, N3)``
    Returns
    -------
    projection : `jnp.ndarray`, shape `(N2, N3)`
        Projection of volume onto imaging plane,
        which is taken to be axis 0.
    """
    N2, N3 = shape
    # Round coordinates for binning
    rounded_coords = jnp.rint(coords).astype(int)
    # Shift coordinates back to zero in the corner, rather than center
    y_coords, z_coords = rounded_coords[:, 1]+N2//2, rounded_coords[:, 2]+N3//2
    # Bin values on the same y-z plane
    flat_coords = jnp.ravel_multi_index((y_coords, z_coords), (N2, N3), mode='clip')
    projection = jnp.bincount(flat_coords, weights=volume, length=N2*N3).reshape((N2, N3))

    return projection


def normalize(image):
    """
    Normalize image.

    Parameters
    ----------


    Returns
    -------

    """
    pass


def noise(image):
    """
    Add Gaussian white noise to image.

    Parameters
    ----------

    Return
    ------

    """
    pass


if __name__ == '__main__':
    from matplotlib import pyplot as plt
    from jax import jit
    from rotations import rotate_rpy
    from interpolation import interpolate
    from template import read_mrc
    from coordinates import coordinatize

    template = read_mrc("./example/6dpu_14pf_bfm1_ps1_1.mrc")
    shape = template.shape[1:]

    # Read coordinates
    model, coords = coordinatize(template)

    # Apply rotation
    rpy = jnp.array([jnp.pi/4, jnp.pi/4, jnp.pi/2])
    rotated_coords = rotate_rpy(coords, rpy)

    # Project
    projection = project(model, rotated_coords, shape)
    image = interpolate(projection, method="linear", fill_value=0.0)
    print((image - projection).max(), (image - projection).min())
    #print(jnp.unique(image, return_counts=True))

    # Normalize
    #image = normalize(image)
    #image = image.at[jnp.where(image != 0)].set(jnp.nan)

    fig, axes = plt.subplots(ncols=3)
    ax1, ax2, ax3 = axes
    ax1.set(title="Projection")
    ax2.set(title="Interpolated projection")
    ax3.set(title="Difference")
    im1 = ax1.imshow(projection, cmap="gray")
    ax2.imshow(image, cmap="gray")
    ax3.imshow(image - projection, cmap="gray")
    # fig.colorbar(im1, ax=ax1)
    plt.show()
