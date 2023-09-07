import numpy as np


def test_update(noisy_model):
    (
        offset_x,
        view_phi,
        voltage,
        N,
        alpha,
        xi,
        pixel_size,
        resolution,
    ) = (
        50.23,
        np.pi / 2.2,
        250.23,
        0.77,
        0.676,
        12342.0,
        4.0,
        4.54,
    )
    params = dict(
        offset_x=offset_x,
        view_phi=view_phi,
        voltage=voltage,
        N=N,
        alpha=alpha,
        xi=xi,
        pixel_size=pixel_size,
        resolution=resolution,
    )
    state = noisy_model.state.update(**params)
    specimen = noisy_model.specimen.update(**params)
    model = noisy_model.update(**params)
    # Test specimen update
    assert resolution == specimen.resolution
    # Test state update
    assert offset_x == state.pose.offset_x
    assert view_phi == state.pose.view_phi
    assert voltage == state.optics.voltage
    assert N == state.exposure.N
    assert alpha == state.detector.variance.alpha
    assert xi == state.ice.variance.xi
    assert pixel_size == state.detector.pixel_size
    # Test model update
    assert offset_x == model.state.pose.offset_x
    assert view_phi == model.state.pose.view_phi
    assert voltage == model.state.optics.voltage
    assert N == model.state.exposure.N
    assert alpha == model.state.detector.variance.alpha
    assert xi == model.state.ice.variance.xi
    assert pixel_size == model.state.detector.pixel_size
