# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


# --------------------
# System wide imports
# -------------------

from enum import Enum
from typing import Tuple

# =====================
# Third party libraries
# =====================

import numpy as np
from numpy.typing import ArrayLike

from astropy.coordinates import Angle
from astropy import units as u

from scipy.interpolate import griddata

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Type annotations
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap

from streamlit.logger import get_logger

from ..lib.dbase.model import observer_name

# ----------------
# Global variables
# ----------------

log = get_logger(__name__)


class Magnitude(float, Enum):
    SUPER_BRIGHT = 8.0
    BRIGHT = 10
    MODERATE = 17
    MEDIUM_DARK = 18.6
    SUPER_DARK = 22.0
    BLACK = 24.0


class Azimuth(Enum):
    N = 0
    NE = 45
    E = 90
    SE = 135
    S = 180
    SW = 225
    W = 270
    NW = 315


# -------------
# Local imports
# -------------


def interpolate(
    azimuths: ArrayLike,  # in degrees
    zenitals: ArrayLike,  # in degrees
    zvalues: ArrayLike,  # can be magnitudes or temperatures
    grid_step: float = 1.0,  # in degrees
) -> Tuple[ArrayLike, ArrayLike, ArrayLike]:
    """Interpolate magnitudes across the azimuth, zenital axis"""

    # Generate a finer grid in zenital and azimuth axis (in degrees)
    zen_axis = np.arange(0, np.max(zenitals) + grid_step, grid_step)
    azi_axis = np.arange(0, 360 + grid_step, grid_step)
    # prepare the bidimensional grid for interpolation
    zen_grid, azi_grid = np.meshgrid(zen_axis, azi_axis)
    # Extend the Azimuths array to -360 to +360 circles
    extended_azi = np.ravel([azimuths - 360, azimuths, azimuths + 360])
    # and duplicate data along the extended azimuth axes
    extended_zen = np.ravel([zenitals, zenitals, zenitals])
    extended_zval = np.ravel([zvalues, zvalues, zvalues])
    # Interpolated magnitudes for the grid points
    interpolated_zval = griddata(
        (extended_zen, extended_azi), extended_zval, (zen_grid, azi_grid), method="cubic"
    )
    # INTERPOLATED zvalues as array instead of meshgrid
    interpolated_zval = np.array(interpolated_zval).reshape(len(azi_axis), len(zen_axis))
    log.info("interpolated_zval = %s", interpolated_zval.shape)
    return np.radians(azi_grid), zen_grid, interpolated_zval


def colormap() -> LinearSegmentedColormap:
    """make a 256 point combined colormap from reversed viridis and YlOrRd"""
    NC1 = 192
    colors2 = plt.cm.viridis_r(np.linspace(0, 1, NC1))
    colors1 = plt.cm.YlOrRd_r(np.linspace(0, 1, 256 - NC1))
    colors = np.vstack((colors1, colors2))
    return mcolors.LinearSegmentedColormap.from_list("my_colormap", colors)


def plot_add_metadata(
    fig: Figure, observation: dict, observer: dict, location: dict, photometer: dict
) -> None:
    latitude = Angle(location["latitude"] * u.deg).to_string(
        precision=0, alwayssign=True,  format="latex_inline"
    )
    longitude = Angle(location["longitude"] * u.deg).to_string(
        precision=0, alwayssign=True,  format="latex_inline"
    )
    fig.text(0.90, 0.28, f"{observation['timestamp_1']}Z", size=14, ha="right")
    fig.text(0.90, 0.26, f"Photometer: {photometer['name']}", size=14, ha="right")
    # fig.text(0.90, 0.17, self.file_txt_reduced, fontsize=12, horizontalalignment="right")
    fig.text(0.12, 0.28, rf"LONG {longitude}", size=14, ha="left")
    fig.text(0.12, 0.26, rf"LAT  {latitude}", size=14, ha="left")
    name = observer_name(observer)[:100]
    fig.text(0.5, 0.96, name, ha="center", size=12)


def plot_non_interpolated(
    tag: str,
    azimuths: ArrayLike,
    zenitals: ArrayLike,
    magnitudes: ArrayLike,
    min_mag: float,
    max_mag: float,
    nticks: int,
) -> Figure:
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(9, 10))
    ax.set_theta_zero_location(Azimuth.N.name)  # Set the north to the north
    ax.set_theta_direction(-1)
    ax.set_xticks(np.deg2rad([e.value for e in Azimuth]))
    ax.set_xticklabels([e.name for e in Azimuth], fontdict={"fontsize": 14})
    ax.tick_params(pad=1.2)
    cmap = colormap()
    cax = ax.scatter(
        np.radians(azimuths),
        zenitals,
        c=magnitudes,
        cmap=cmap,
        vmin=min_mag,
        vmax=max_mag,
        linewidth=5,
    )
    ticks = np.linspace(min_mag, max_mag, num=nticks, endpoint=True)
    # Draw the color bar
    cb = fig.colorbar(cax, orientation="horizontal", fraction=0.35, ticks=ticks, pad=0.08)
    cb.set_label("Sky Brightness [mag/arcsec$^2$]", fontsize=14)
    cb.ax.tick_params(labelsize=12)
    # Cut the axes to fit data
    ax.set_ylim(0, max(zenitals))
    ax.set_title(tag, size=15)  # 25
    return fig


def plot_interpolated(
    tag: str,
    azimuths: ArrayLike,
    zenitals: ArrayLike,
    magnitudes: ArrayLike,
    min_mag: float,
    max_mag: float,
    nticks: int,  # Number of xticks labels to avoid crowding
    dark_mag: float = Magnitude.BRIGHT,  # Threshold magnitude for brightness cmap steps
    thres_mag: float = Magnitude.MEDIUM_DARK,  # Threshold magnitude for brightness cmap steps
) -> Figure:
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(9, 12))
    ax.set_theta_zero_location(Azimuth.N.name)  # Set the north to the north
    ax.set_theta_direction(-1)
    ax.set_xticks(np.deg2rad([e.value for e in Azimuth]))
    ax.set_xticklabels([e.name for e in Azimuth], fontdict={"fontsize": 14})
    ax.tick_params(pad=1.2)
    cmap = colormap()
    # Plot the TAS data as tiny red dots for reference
    ax.scatter(np.radians(azimuths), zenitals, c="red", zorder=2, s=8)
    azi_grid, zen_grid, interp_mag = interpolate(azimuths, zenitals, zvalues=magnitudes)
    m_step_1 = 0.2  # 0.2 initial step in contour levels
    m_step_2 = 0.4
    if np.max(magnitudes) > dark_mag:  # 21 dark place
        lev_c_b = np.arange(thres_mag, max_mag + m_step_1 + 0.1, m_step_1)
        # more width between contour line for lower magnitudes
        lev_c_a = np.arange(min_mag, thres_mag, m_step_2)
        lev_f = np.arange(min_mag, max_mag + m_step_1 + 0.1, m_step_2)
    else:
        lev_f = np.arange(min_mag, max_mag, m_step_1)  # visible contour lines
    cb_ticks = np.round(np.linspace(min_mag, max_mag, num=nticks, endpoint=True), 1)
    cax = ax.contourf(
        azi_grid,
        zen_grid,
        interp_mag,
        levels=lev_f,
        cmap=cmap,
        vmin=min_mag,
        vmax=max_mag,
    )
    cax_lines = ax.contour(cax, colors="w", levels=lev_c_b, linewidths=2)
    ax.clabel(
        cax_lines,
        colors="w",
        inline=True,
        fmt="%1.1f",
        rightside_up=True,
        fontsize="medium",
    )
    cax_lines = ax.contour(cax, colors="k", levels=lev_c_a, linewidths=1)
    ax.clabel(
        cax_lines,
        colors="k",
        inline=True,
        fmt="%1.1f",
        rightside_up=True,
        fontsize="medium",
    )
    # extra contour lines over 22 mag/arcsec2
    high_levels = np.arange(Magnitude.SUPER_DARK, Magnitude.BLACK, m_step_2)
    cax_lines = ax.contour(cax, colors="k", levels=high_levels, linewidths=1)
    ax.clabel(
        cax_lines,
        colors="k",
        inline=True,
        fmt="%1.1f",
        rightside_up=True,
        fontsize="medium",
    )
    # extra contour lines below 17 mag/arcsec2
    low_levels = np.arange(Magnitude.SUPER_BRIGHT, Magnitude.MODERATE, 1)
    cax_lines = ax.contour(cax, colors="k", levels=low_levels, linewidths=0.5)
    ax.clabel(
        cax_lines,
        colors="k",
        inline=True,
        fmt="%1.1f",
        rightside_up=True,
        fontsize="small",
    )
    # Draw the color bar
    cb = fig.colorbar(cax, orientation="horizontal", fraction=0.35, ticks=cb_ticks, pad=0.08)
    cb.set_label("Sky Brightness [mag/arcsec$^2$]", fontsize=14)
    cb.ax.tick_params(labelsize=12)
    # Cut the axes to fit data
    ax.set_ylim(0, max(zenitals))
    ax.set_title(tag, size=15)  # 25
    return fig


def plot(
    tag: str,
    azimuths: ArrayLike,
    zenitals: ArrayLike,
    magnitudes: ArrayLike,
    min_mag: float = Magnitude.MODERATE,
    max_mag: float = Magnitude.SUPER_DARK,
    nticks: int = 12,  # Number of xticks labels to avoid crowding
    thr_mag: float = 10,  # Threshold magnitude for brightness cmap steps
    interpolated: bool = True,
    observation: dict = None,  # Additional observation metadata
    observer: dict = None,  # Additional observer metadata
    location: dict = None,  # Additional location metadata
    photometer: dict = None,  # Additional photometer metadata
) -> Figure:
    """Produce a color map of sky night brightness"""
    fig = (
        plot_interpolated(
            tag=tag,
            azimuths=azimuths,
            zenitals=zenitals,
            magnitudes=magnitudes,
            min_mag=min_mag,
            max_mag=max_mag,
            nticks=nticks,
        )
        if interpolated
        else plot_non_interpolated(
            tag=tag,
            azimuths=azimuths,
            zenitals=zenitals,
            magnitudes=magnitudes,
            min_mag=min_mag,
            max_mag=max_mag,
            nticks=nticks,
            thr_mag=thr_mag,
        )
    )
    if observation is not None:
        assert observer is not None
        assert location is not None
        assert photometer is not None
        plot_add_metadata(fig, observation, observer, location, photometer)
    return fig


def plot_alex(
    tag: str,
    azimuths: ArrayLike,
    zenitals: ArrayLike,
    magnitudes: ArrayLike,
    min_mag: float = 15,
    max_mag: float = 25,
    interpolated: bool = False,
    cmap: str = "viridis_s",
) -> Figure:
    """Produce a color map of sky night brightness"""

    r_points = zenitals
    theta_points = np.deg2rad(azimuths)
    mag_points = magnitudes

    r_lin = np.linspace(0, 90, 500)
    theta_lin = np.linspace(0, 2 * np.pi, 500)
    theta_grid, r_grid = np.meshgrid(theta_lin, r_lin)

    interp_cubic = griddata(
        (theta_points, r_points), mag_points, (theta_grid, r_grid), method="cubic"
    )
    interp_nearest = griddata(
        (theta_points, r_points), mag_points, (theta_grid, r_grid), method="nearest"
    )
    brightness = np.where(np.isnan(interp_cubic), interp_nearest, interp_cubic)

    # === GRAFICAR ===
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 8))
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)

    cmap = plt.get_cmap("viridis_r")
    norm = mcolors.Normalize(vmin=17, vmax=22.2)
    contourf = ax.contourf(theta_grid, r_grid, brightness, 100, cmap=cmap, norm=norm)
    contour_lines = ax.contour(
        theta_grid,
        r_grid,
        brightness,
        levels=np.arange(17.0, 22.2, 0.2),
        colors="white",
        linewidths=0.4,
    )
    ax.clabel(contour_lines, fmt="%.1f", fontsize=7)

    ax.scatter(theta_points, r_points, c="red", s=4)
    ax.set_rlim(0, 90)
    ax.set_rticks(np.arange(10, 91, 10))
    ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels(["E", "NE", "N", "NW", "W", "SW", "S", "SE"])

    ax.set_title(tag, fontsize=14, pad=20)
    cbar_ax = fig.add_axes([0.2, 0.03, 0.6, 0.025])
    cbar = plt.colorbar(
        contourf, cax=cbar_ax, orientation="horizontal", ticks=np.arange(17, 22.5, 0.5)
    )
    cbar.set_label("Sky Brightness [mag/arcsec²]", fontsize=10)
    return fig
