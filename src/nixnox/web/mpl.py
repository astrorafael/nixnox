# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


# --------------------
# System wide imports
# -------------------


# =====================
# Third party libraries
# =====================

import numpy as np
from numpy.typing import ArrayLike

from scipy.interpolate import griddata

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.figure import Figure

# -------------
# Local imports
# -------------


def plot(
    tag: str,
    azimuths: ArrayLike,
    zenitals: ArrayLike,
    magnitudes: ArrayLike,
    min_mag: float = 15,
    max_mag: float = 25,
    cmap: str = "viridis_s",
    interpolated: bool = False,
) -> Figure:
    """Produce a color map of sky night brightness"""

    nticks = 12  # Number of xticks labels to avoid crowding
    m_step_1 = 0.2  # 0.2 initial step in contour levels
    m_step_2 = 0.4
    # self.levels = levels    # not used
    lev_c = np.arange(min_mag, max_mag, m_step_1)  # visible contour lines
    lev_f = lev_c  # np.arange(min_mag,max_mag,m_step_1)       # contour colors

    if np.max(magnitudes) > 10:  # 21 dark place
        lev_c_b = np.arange(18.6, max_mag + m_step_1 + 0.1, m_step_1)
        lev_c_a = np.arange(
            min_mag, 18.6, m_step_2
        )  # more width between contour line for lower magnitudes
        lev_c = np.concatenate([lev_c_a, lev_c_b])
        lev_f = np.arange(min_mag, max_mag + m_step_1 + 0.1, m_step_2)
    lev_f_ticks = lev_f
    if len(lev_f) > nticks:  # reduce number of ticks to avoid crowdind in cbar
        lev_f_ticks = np.arange(min_mag, max_mag + m_step_1 + 0.1, m_step_1 * 2)

        # RFG
        # self.lev_f = lev_f
        # self.lev_c = lev_c

    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(9, 10))
    # fig.patch.set_facecolor('lightblue')  #Background color, not used
    ax.set_theta_zero_location("N")  # Set the north to the north
    ax.set_theta_direction(-1)
    ax.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontdict={"fontsize": 16})
    ax.tick_params(pad=1.2)
    # make a 256 point combined colormap from reversed viridis and YlOrRd
    NC1 = 192
    colors2 = plt.cm.viridis_r(np.linspace(0, 1, NC1))
    colors1 = plt.cm.YlOrRd_r(np.linspace(0, 1, 256 - NC1))
    colors = np.vstack((colors1, colors2))
    cmap = mcolors.LinearSegmentedColormap.from_list("my_colormap", colors)
    #################################

    if interpolated:
        __interpolate_measurements__()

        try:
            """Interpolated map"""
            cax = ax.contourf(
                self.i_azimuths,
                self.i_zeniths,
                self.i_magnitudes,
                self.lev_f,
                cmap=cmap,
                vmin=min_mag,
                vmax=max_mag,
            )

        except:
            print("ERROR: Interpolated values not found.\n")
            print(
                'Try ".interpolate_measurements()" method for generating interpolated Magnitude Map before.\n'
            )

        try:
            """Measured points for reference"""
            ax.scatter(np.radians(self.azimuths), self.zeniths, c="red", zorder=2, s=8)
        except Exception:
            print("ERROR: It was not possible to draw reference measured points")

        try:
            """Contour lines"""
            smallest_mag = np.min(self.i_magnitudes)
            biggest_mag = np.nanmax(self.i_magnitudes)

            if biggest_mag > 20:
                line_color = "w"
            else:
                line_color = "#2F82C2"
            # cax_lines = ax.contour(cax, colors=line_color, levels=self.lev_c,linewidths=2)
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
            high_levels = np.arange(22.0, 24, 0.4)
            cax_lines = ax.contour(cax, colors="k", levels=high_levels, linewidths=1)
            ax.clabel(
                cax_lines,
                colors="k",
                inline=True,
                fmt="%1.1f",
                rightside_up=True,
                fontsize="medium",
            )
            # extra contour lines bellow 17 mag/arcsec2
            low_levels = np.arange(8.0, 17.0, 1)
            cax_lines = ax.contour(cax, colors="k", levels=low_levels, linewidths=0.5)
            ax.clabel(
                cax_lines,
                colors="k",
                inline=True,
                fmt="%1.1f",
                rightside_up=True,
                fontsize="small",
            )

        except Exception:
            print("ERROR: It was not possible to draw contour lines")

    else:
        cax = ax.scatter(
            np.radians(azimuths),
            zenitals,
            c=magnitudes,
            cmap=cmap,
            vmin=min_mag,
            vmax=max_mag,
        )

        """Colorbar"""
        cb = fig.colorbar(
            cax, orientation="horizontal", fraction=0.048, ticks=lev_f_ticks, pad=0.08
        )
        cb.set_label("Sky Brightness [mag/arcsec$^2$]", fontsize=17)
        cb.ax.tick_params(labelsize=12)

        """Cut the axes to fit data"""
        ax.set_ylim(0, max(zenitals) + 0.0)
        ax.set_title(tag, size=25)  # 25
        return fig
    return None


def plot(
    tag: str,
    azimuths: ArrayLike,
    zenitals: ArrayLike,
    magnitudes: ArrayLike,
    min_mag: float = 15,
    max_mag: float = 25,
    cmap: str = "viridis_s",
    interpolated: bool = False,
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
