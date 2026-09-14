import glob
import os
import arrow
import meshio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from matplotlib.colors import ListedColormap, BoundaryNorm

todaysdate = arrow.now().format('YYYYMMDD')

def plot_wave_height_and_period(vtu_file):

    # ---------------------------------------------------------
    # Read VTU
    # ---------------------------------------------------------
    mesh = meshio.read(vtu_file)

    points = mesh.points
    x = points[:, 0]
    y = points[:, 1]

    # Triangular connectivity
    triangles = mesh.cells_dict["triangle"]

    # Extract SWAN variables
    hs_meters = mesh.point_data["Hsig"]
    hs_feet = hs_meters * 3.28084

    wdir_deg = mesh.point_data["PkDir"]
    tpsmoo = mesh.point_data["Tm01"]  # Smoothed Peak Wave Period (seconds)

    # Extract Bathymetry/Depth (Update "Depth" to "Dep" if your mesh key is different)
    depth = mesh.point_data["Depth"]

    triang = tri.Triangulation(x, y, triangles)

    # ---------------------------------------------------------
    # Map 1 Layout Setup: Wave Height (NOAA 15-color Palette)
    # ---------------------------------------------------------
    colors_hs = [
        "#000080", "#0033cc", "#0066ff", "#00ccff", "#00ffff",
        "#00ff99", "#00ff00", "#66ff00", "#ccff00", "#ffff00",
        "#ffcc00", "#ff9900", "#ff6600", "#ff0000", "#cc0000",
    ]
    cmap_hs = ListedColormap(colors_hs)
    levels_hs = np.arange(0, 7.5, 0.5)
    norm_hs = BoundaryNorm(levels_hs, cmap_hs.N)

    # ---------------------------------------------------------
    # Map 2 Layout Setup: Detailed Wave Period (5 to 11 Seconds)
    # ---------------------------------------------------------
    base_cmap_tp = plt.colormaps['plasma']
    levels_tp = np.arange(5, 11.1, 0.2)
    cmap_tp = base_cmap_tp.resampled(len(levels_tp) - 1)
    norm_tp = BoundaryNorm(levels_tp, cmap_tp.N)

    # ---------------------------------------------------------
    # Bathymetry Contour Levels
    # Define depths to draw lines at (e.g., 5m, 10m, 20m, 50m, 100m)
    # ---------------------------------------------------------
    bathy_levels = [5.0, 20.0]

    # ---------------------------------------------------------
    # Setup Figure Frame (1 Row, 2 Columns Side-by-Side)
    # ---------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(
        1, 2,
        figsize=(22, 11),  # Wide format layout to fit both maps comfortably
        facecolor="lightgray"
    )

    # =========================================================
    # LEFT PANEL: SIGNIFICANT WAVE HEIGHT & DIRECTION
    # =========================================================
    # 1. Filled Contours
    cf1 = ax1.tricontourf(
        triang, hs_feet,
        levels=levels_hs, cmap=cmap_hs, norm=norm_hs, extend="max"
    )
    # 2. Black Wave Height Contour Lines
    ax1.tricontour(
        triang, hs_feet,
        levels=np.arange(0, 7.5, 1.0), colors="k", linewidths=0.3
    )

    # 3. Bathymetry Contour Overlays
    contour_bathy1 = ax1.tricontour(
        triang, depth,
        levels=bathy_levels, colors="#555555", linestyles="dashed", linewidths=0.6
    )
    ax1.clabel(contour_bathy1, inline=True, fmt="%d m", fontsize=8, colors="#555555")

    # 4. Vector Directional Arrows
    rad = np.deg2rad(wdir_deg)
    u = np.cos(rad)
    v = np.sin(rad)

    stride = 100000
    mask = hs_feet > 0.05

    ax1.quiver(
        x[mask][::stride], y[mask][::stride],
        u[mask][::stride], v[mask][::stride],
        color="white", edgecolor="black", linewidth=0.6,
        scale=35, width=0.0035, headwidth=4, pivot="middle"
    )

    ax1.set_aspect("equal")
    ax1.set_title("Significant Wave Height (ft)", fontsize=14, fontweight="bold")

    # Left Colorbar
    cbar1 = fig.colorbar(cf1, ax=ax1, orientation="horizontal", pad=0.06, fraction=0.045)
    cbar1.set_label("Wave Height (ft)", fontsize=11)

    # =========================================================
    # RIGHT PANEL: HIGH-RESOLUTION WAVE PERIOD (TPSmoo)
    # =========================================================
    # 1. Filled Contours
    cf2 = ax2.tricontourf(
        triang, tpsmoo,
        levels=levels_tp, cmap=cmap_tp, norm=norm_tp, extend="both"
    )
    # 2. Black Wave Period Contour Lines
    ax2.tricontour(
        triang, tpsmoo,
        levels=np.arange(5, 11.1, 1.0), colors="k", linewidths=0.4, alpha=0.7
    )

    # 3. Bathymetry Contour Overlays
    contour_bathy2 = ax2.tricontour(
        triang, depth,
        levels=bathy_levels, colors="#444444", linestyles="dashed", linewidths=0.6
    )
    ax2.clabel(contour_bathy2, inline=True, fmt="%d m", fontsize=8, colors="#444444")

    ax2.set_aspect("equal")
    ax2.set_title("Mean Wave Period (s)", fontsize=14, fontweight="bold")

    # Right Colorbar
    cbar2 = fig.colorbar(
        cf2, ax=ax2, orientation="horizontal", pad=0.06, fraction=0.045,
        ticks=np.arange(5, 11.1, 1.0), format="%.1f"
    )
    cbar2.set_label("Wave Period (seconds)", fontsize=11)

    # ---------------------------------------------------------
    # Format Grid & Axis Labels on Both Maps
    # ---------------------------------------------------------
    for ax in [ax1, ax2]:
        ax.tick_params(axis='both', which='major', labelsize=9, colors='#333333')
        ax.get_xaxis().get_major_formatter().set_scientific(False)
        ax.get_yaxis().get_major_formatter().set_scientific(False)
        ax.grid(True, linestyle="--", alpha=0.5, color="gray", linewidth=0.5)

    # Overall Global Title
    fig.suptitle(
        f"SWAN Model Output Analysis\n{os.path.basename(vtu_file)}",
        fontsize=18, fontweight="bold", y=0.96
    )

    plt.tight_layout(rect=[0, 0, 1, 0.93])

    png_name = os.path.splitext(vtu_file)[0] + "_combined.png"
    plt.savefig(png_name, dpi=300, bbox_inches="tight", facecolor="lightgray")
    plt.close()

    print("Saved combined plot with bathymetry:", png_name)


# ---------------------------------------------------------
# Process all files
# ---------------------------------------------------------
for vtu in glob.glob(f"{todaysdate}/*.vtu"):
    plot_wave_height_and_period(vtu)
