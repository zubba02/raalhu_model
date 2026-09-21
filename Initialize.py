import wget
import shutil
import arrow
import schedule
import time
import os
import xarray as xr
import glob
import numpy as np
import subprocess
import pyvista as pv
import meshio
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from matplotlib.colors import ListedColormap, BoundaryNorm

#https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20250309/00/wave/gridded/gfswave.t00z.global.0p16.f000.grib2

todaysdate = arrow.now().format('YYYYMMDD')

#todaysdate = '20260902'

def get_gfs_grib():

    print("Attempting to execute task downloading the global data at:", time.strftime("%H:%M:%S"))

    output_directory = os.mkdir('{}'.format(todaysdate))

    for i in range(1,23,1):

        print ('DOWNLOADING FORECAST : {:03d}z'.format(i))

        url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{}/00/wave/gridded/gfswave.t00z.global.0p16.f{:03d}.grib2".format(todaysdate, i)

        print ('Downloaded forecast : {}'.format(url))

        filename = wget.download(url, out='{}'.format(todaysdate))

        print ('\n')



def get_bund_valss():

    f = glob.iglob('{}/*.grib2'.format(todaysdate))

    bunds = [101,102,103,104]

    for i in f:

        print ('LOADING GRIB FILE {}'.format(i))

        ds = xr.open_dataset("{}".format(i))

        print ('COMPLETED LOADING GRIB FILE {}'.format(i))

        bund_forcing_swh = []

        bund_forcing_perpw = []

        bund_forcing_dirpw = []

        for k in bunds:

            print('EVALUATING GRIB FILE {} AT  BUND VALUES FOR BUND {}'.format(i, k))

            print ('LOADING THE BUND  FILE {}.csv'.format(k))

            current_bund = np.loadtxt('INITIALISATION/FORCING_BUND_COORDS/{}.csv'.format(k), delimiter=',',skiprows=1)

            bund_all_swh = []

            bund_all_perpw = []

            bund_all_dirpw = []

            for j in current_bund:

                #print (j[2], j[3])

                swh = ds.sel(latitude=j[3], longitude=j[2], method="nearest")['swh'].values

                perpw = ds.sel(latitude=j[3], longitude=j[2], method="nearest")['perpw'].values

                dirpw = ds.sel(latitude=j[3], longitude=j[2], method="nearest")['dirpw'].values

                bund_all_swh.append(swh)

                bund_all_perpw.append(perpw)

                bund_all_dirpw.append(dirpw)

            bund_forcing_swh.append(np.max(bund_all_swh))

            bund_forcing_perpw.append(np.max(bund_all_perpw))

            bund_forcing_dirpw.append(np.max(bund_all_dirpw))

        print ('{} Hs (swell + wind waves) is {}'.format(i ,bund_forcing_swh))

        print ('{} median period (swell + wind waves) is {}'.format(i ,bund_forcing_perpw))

        print ('{} direction (swell + wind waves) is {}'.format(i ,bund_forcing_dirpw))

        bund_forcing_swh = np.array(bund_forcing_swh)

        bund_forcing_perpw = np.array(bund_forcing_perpw)

        bund_forcing_dirpw = np.array(bund_forcing_dirpw)

        np.savetxt('{}_FORCING_swh.csv'.format(i),bund_forcing_swh, delimiter=',' )

        np.savetxt('{}_FORCING_perpw.csv'.format(i),bund_forcing_perpw, delimiter=',' )

        np.savetxt('{}_FORCING_dirpw.csv'.format(i),bund_forcing_dirpw, delimiter=',' )



def get_winds():

    print ("EVALUATING FOR WIND")

    grib_files = glob.iglob('{}/*.grib2'.format(todaysdate))

    for i in grib_files:

        print ("EVALUATING FOR WIND AT GRIB FILE {}".format(i))

        ds = xr.open_dataset("{}".format(i))

        wind_val = ds.sel(latitude=1.90, longitude=73.40, method="nearest")['ws'].values

        wind_dir = ds.sel(latitude=1.90, longitude=73.40, method="nearest")['wdir'].values

        with open('{}_FORCING_wind.csv'.format(i), "w") as f:

            f.write("{}\n".format(wind_val))

        with open('{}_FORCING_dir.csv'.format(i), "w") as f:

            f.write("{}\n".format(wind_dir))




def write_run_file():

    all_times = ['f{:03}'.format(i) for i in range(1,23,1)]

    for j in all_times :

        direction = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_dirpw.csv'.format(todaysdate,j), delimiter=',')

        period = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_perpw.csv'.format(todaysdate,j), delimiter=',')

        wave_height = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_swh.csv'.format(todaysdate,j), delimiter=',')

        wind_speed = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_wind.csv'.format(todaysdate,j), delimiter=',')

        wind_direction = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_dir.csv'.format(todaysdate,j), delimiter=',')



        print ("Writting run files for forecase hour {}".format(j))

        f = open("{}/{}.swn".format(todaysdate,j), "w")

        f.write('$****************LAAMU {} {} ****************************************'.format(todaysdate, j))

        f.write('\n')
        f.write('\n')

        f.write('PROJ \'LAAMU_{}\' \'{}\''.format(todaysdate, j))

        f.write('\n')

        f.write('\n')

        f.write('SET depmin 0.0 NAUTICAL')

        f.write('\n')
        f.write('\n')

        f.write('$CGRID 295668.0 191709.0 0. 55000.00 52000.00 100 100 CIRCLE 36 0.0521 1. 31')

        f.write('\n')

        f.write('CGRID UNSTRUCTURED CIRCLE 36 0.0521 1. 31')
        f.write('\n')
        f.write('\n')

        f.write('READ UNSTRUCTURED triangle \'../INITIALISATION/MESH_BATHY/TEST.4\'')

        f.write('\n')
        f.write('\n')

        f.write('INPgrid BOTtom REGular 295668.0 191709.0 0. 999 999 55. 55. EXCeption 999999.00')
        f.write('\n')
        f.write('READinp BOTtom -1. \'../INITIALISATION/MESH_BATHY/clippedbathy_1000_1000.csv\' 4 FREE')

        f.write('\n')
        f.write('\n')

        f.write('BOUN SHAPE JON 3.3 PEAK DSPR DEGREES')
        f.write('\n')
        f.write('BOUN SIDE 101 CONST PAR {} {} {} 30'.format(wave_height[0],period[0],direction[0]))
        f.write('\n')
        f.write('BOUN SIDE 102 CONST PAR {} {} {} 30'.format(wave_height[1],period[1],direction[1]))
        f.write('\n')
        f.write('BOUN SIDE 103 CONST PAR {} {} {} 30'.format(wave_height[2],period[2],direction[2]))
        f.write('\n')
        f.write('BOUN SIDE 104 CONST PAR {} {} {} 30'.format(wave_height[3],period[3],direction[3]))

        f.write('\n')
        f.write('\n')

        f.write('WIND {} {}'.format(wind_speed,wind_direction))
        f.write('\n')
        f.write('\n')

        f.write('GEN3 JANSSEN 4.5 0.5 AGROW 0.003')
        f.write('\n')
        f.write('QUAD')
        f.write('\n')
        f.write('BREA')
        f.write('\n')
        f.write('WCAP')
        f.write('\n')
        f.write('\n')
        f.write('$********************* OUTPUT REQUESTS *************************')
        f.write('\n')
        f.write('\n')
        f.write('BLOCK  \'COMPGRID\' NOHEAD \'Laamu_{}_{}.vtu\' LAYOUT 3 XP YP BOTLEV WATLEV DEPTH HS TM01 DSPR PDIR VEL FRCOEFF TPS URMS'.format(todaysdate,j))
        f.write('\n')
        f.write('TEST 1,0')
        f.write('\n')
        f.write('NUMERIC STOPC 0.5 0.5 0.95 1')
        f.write('\n')
        f.write('COMPUTE')
        f.write('\n')
        f.write('STOP')

        f.close()


def run_files():

    original_dir = os.getcwd()

    all_swan_files = ['f{:03}.swn'.format(i) for i in range(1,23,1)]

    with open('{}/run_all.sh'.format(todaysdate), 'w') as r:

        for k in all_swan_files:

            r.write('swanrun -input {}'.format(k))

            r.write('\n')

    os.chdir('{}'.format(todaysdate))

    subprocess.call('./run_all.sh', shell=True)

    os.chdir(original_dir)


def run_files_powershell():

    original_dir = os.getcwd()

    all_swan_files = ['f{:03}.swn'.format(i) for i in range(1,2,1)]

    with open('{}/run_all.ps1'.format(todaysdate), 'w') as r:

        for k in all_swan_files:

            r.write('swanrun {} 12'.format(k)[:12])

            r.write('\n')

    os.chdir('{}'.format(todaysdate))

    subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "run_all.ps1"])

    os.chdir(original_dir)



def make_png():
    vtu_files = glob.iglob('{}/*.vtu'.format(todaysdate))
    for k in vtu_files :
        mesh = pv.read("{}".format(k))
        print("Point data:", mesh.point_data.keys())
        print("Cell data:", mesh.cell_data.keys())

        plotter = pv.Plotter(off_screen=True, window_size=(3000, 3000))

        plotter.add_mesh(mesh,scalars="Hsig",clim=(0, 2),cmap="turbo",show_edges=False,
        scalar_bar_args={
            "title": "Hsig (m)",
            "title_font_size": 50,
            "label_font_size": 50,
            "fmt": "%.1f",
            "position_x": 0.2,
            "position_y": 0.01,
            "vertical": False,
        })
        plotter.view_xy()
        plotter.camera.Zoom(1.2)
        plotter.show(screenshot="{}.png".format(k))


def plot_wave_height_and_period(vtu_file):

    mesh = meshio.read(vtu_file)

    points = mesh.points
    x = points[:, 0]
    y = points[:, 1]

    triangles = mesh.cells_dict["triangle"]

    hs_meters = mesh.point_data["Hsig"]
    hs_feet = hs_meters * 3.28084

    wdir_deg = mesh.point_data["PkDir"]
    tpsmoo = mesh.point_data["Tm01"]

    depth = mesh.point_data["Depth"]

    triang = tri.Triangulation(x, y, triangles)

    colors_hs = [
        "#000080", "#0033cc", "#0066ff", "#00ccff", "#00ffff",
        "#00ff99", "#00ff00", "#66ff00", "#ccff00", "#ffff00",
        "#ffcc00", "#ff9900", "#ff6600", "#ff0000", "#cc0000",
    ]
    cmap_hs = ListedColormap(colors_hs)
    levels_hs = np.arange(0, 7.0, 0.5)
    norm_hs = BoundaryNorm(levels_hs, cmap_hs.N)

    base_cmap_tp = plt.colormaps['plasma']
    levels_tp = np.arange(5, 10.0, 0.2)
    cmap_tp = base_cmap_tp.resampled(len(levels_tp) - 1)
    norm_tp = BoundaryNorm(levels_tp, cmap_tp.N)


    bathy_levels = [5.0, 20.0]


    fig, (ax1, ax2) = plt.subplots(
        1, 2,
        figsize=(22, 11),
        facecolor="lightgray"
    )


    cf1 = ax1.tricontourf(
        triang, hs_feet,
        levels=levels_hs, cmap=cmap_hs, norm=norm_hs, extend="max"
    )

    ax1.tricontour(
        triang, hs_feet,
        levels=np.arange(0, 7.5, 1.0), colors="k", linewidths=0.3
    )


    contour_bathy1 = ax1.tricontour(
        triang, depth,
        levels=bathy_levels, colors="#555555", linestyles="dashed", linewidths=0.6
    )
    ax1.clabel(contour_bathy1, inline=True, fmt="%d m", fontsize=8, colors="#555555")

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

    cbar1 = fig.colorbar(cf1, ax=ax1, orientation="horizontal", pad=0.06, fraction=0.045)
    cbar1.set_label("Wave Height (ft)", fontsize=11)

    cf2 = ax2.tricontourf(
        triang, tpsmoo,
        levels=levels_tp, cmap=cmap_tp, norm=norm_tp, extend="both"
    )

    ax2.tricontour(
        triang, tpsmoo,
        levels=np.arange(5, 11.1, 1.0), colors="k", linewidths=0.4, alpha=0.7
    )

    contour_bathy2 = ax2.tricontour(
        triang, depth,
        levels=bathy_levels, colors="#444444", linestyles="dashed", linewidths=0.6
    )
    ax2.clabel(contour_bathy2, inline=True, fmt="%d m", fontsize=8, colors="#444444")

    ax2.set_aspect("equal")
    ax2.set_title("Mean Wave Period (s)", fontsize=14, fontweight="bold")

    cbar2 = fig.colorbar(
        cf2, ax=ax2, orientation="horizontal", pad=0.06, fraction=0.045,
        ticks=np.arange(5, 11.1, 1.0), format="%.1f"
    )
    cbar2.set_label("Wave Period (seconds)", fontsize=11)

    for ax in [ax1, ax2]:
        ax.tick_params(axis='both', which='major', labelsize=9, colors='#333333')
        ax.get_xaxis().get_major_formatter().set_scientific(False)
        ax.get_yaxis().get_major_formatter().set_scientific(False)
        ax.grid(True, linestyle="--", alpha=0.5, color="gray", linewidth=0.5)

    fig.suptitle(
        f"Maldives Experimental Wave Forecast System (MEWFS) Output\n{os.path.basename(vtu_file)}",
        fontsize=18, fontweight="bold", y=0.96
    )

    plt.tight_layout(rect=[0, 0, 1, 0.93])

    png_name = os.path.splitext(vtu_file)[0] + "_combined.png"
    plt.savefig(png_name, dpi=300, bbox_inches="tight", facecolor="lightgray")
    plt.close()

    print("Saved combined plot with bathymetry:", png_name)


def make_height_and_period():
    for vtu in glob.glob(f"{todaysdate}/*.vtu"):
        plot_wave_height_and_period(vtu)




def copy_pngs_to_web_folder():

    script_dir = os.path.dirname(os.path.abspath(__file__))

    date_folder = arrow.now().format("YYYYMMDD")

    destination = os.path.join(
        script_dir,
        "raalhu_web",
        "images",
        "Laamu",
        date_folder
    )

    os.makedirs(destination, exist_ok=True)

    png_files = glob.glob(f"{todaysdate}/*.png")

    print(f"Found {len(png_files)} PNG files")

    for png in png_files:

        shutil.copy2(png, destination)

        print(f"Copied {os.path.basename(png)}")

    print(f"Files copied to {destination}")


def run_git_upload_ps():

    original_dir = os.getcwd()

    os.chdir(f"raalhu_web")

    subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "git_upload.ps1"])

    os.chdir(original_dir)


def run_git_upload():

    original_dir = os.getcwd()

    os.chdir(f"raalhu_web")

    subprocess.call('./git_upload.sh', shell=True)

    os.chdir(original_dir)



#schedule.every(1).seconds.do(write_run_file)

#schedule.every(1).seconds.do(run_files)


#schedule.every(1).seconds.do(get_gfs_grib)

#schedule.every(1).seconds.do(get_bund_valss)

#schedule.every(1).seconds.do(get_winds)

#schedule.every(1).seconds.do(write_run_file)

#schedule.every(1).seconds.do(run_files)

#schedule.every(1).seconds.do(run_files_powershell)

#schedule.every(1).seconds.do(make_png)

#schedule.every(1).seconds.do(make_height_and_period)

schedule.every(1).seconds.do(copy_pngs_to_web_folder)

schedule.every(1).seconds.do(run_git_upload_ps)




'''
schedule.every().day.at('21:00').do(get_gfs_grib)

schedule.every().day.at('21:05').do(get_bund_valss)

schedule.every().day.at('21:10').do(write_run_file)

schedule.every().day.at('21:15').do(run_files)


'''

while True:
    schedule.run_pending()
    time.sleep(1)
