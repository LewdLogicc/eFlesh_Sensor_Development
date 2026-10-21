#!/usr/bin/env python

import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
from anyskin import AnySkinProcess


def visualize(port="/dev/ttyACM0", scaling=70.0):
    sensor_stream = AnySkinProcess(
        num_mags=5,
        port=port,
    )

    sensor_stream.start()
    time.sleep(1.0)


    baseline_samples = sensor_stream.get_data(num_samples=10)
    baseline_samples = np.array(baseline_samples)[:, 1:]
    baseline = np.mean(baseline_samples, axis=0)

    cube_size = 60.0
    half = cube_size / 2.0

    grid_points = 40
    x = np.linspace(-half, half, grid_points)
    y = np.linspace(-half, half, grid_points)
    X, Y = np.meshgrid(x, y)

    sensor_positions = np.array([
        [0.0,   0.0],
        [-18.0, 0.0],
        [18.0,  0.0],
        [0.0,   18.0],
        [0.0,  -18.0],
    ])

    sensor_labels = ["mag0", "mag1", "mag2", "mag3", "mag4"]

    contact_dent_width = 20.0
    no_contact_threshold = 200.0

    plt.ion()
    plt.rcParams["figure.raise_window"] = False

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    running = True

    def on_close(event):
        nonlocal running
        running = False

    fig.canvas.mpl_connect("close_event", on_close)

    def setup_axes():
        ax.set_xlim(-45, 45)
        ax.set_ylim(-45, 45)
        ax.set_zlim(-45, 45)

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Deformation")

        ax.set_title("eFlesh Surface Deformation - Mathematical Model")
        ax.view_init(elev=28, azim=45)

    def calculate_deformed_surface(data):
        data = data.reshape(-1, 3).copy()

        data[:, :2] *= -1

        magnitudes = np.linalg.norm(data, axis=1)

        total_norm = np.linalg.norm(data.flatten())

        Z_top = np.ones_like(X) * half

        if total_norm < no_contact_threshold:
            return Z_top, magnitudes, np.array([0.0, 0.0])

        centre = magnitudes[0]
        left = magnitudes[1]
        right = magnitudes[2]
        top = magnitudes[3]
        bottom = magnitudes[4]

        side_sum = left + right + top + bottom + 1e-6

        estimated_x = (right - left) / side_sum * half
        estimated_y = (top - bottom) / side_sum * half

        estimated_xy = np.array([estimated_x, estimated_y])

        contact_strength = np.mean(magnitudes)
        contact_depth = contact_strength / scaling

        distance_squared = (
            (X - estimated_xy[0]) ** 2
            + (Y - estimated_xy[1]) ** 2
        )

        contact_dent = contact_depth * np.exp(
            -distance_squared / (2 * contact_dent_width ** 2)
        )

        Z_top -= contact_dent

        Z_top -= contact_strength / (scaling * 8.0)

        return Z_top, magnitudes, estimated_xy

    def draw_cube(data):
        ax.cla()
        setup_axes()

        Z_top, magnitudes, estimated_xy = calculate_deformed_surface(data)

        ax.plot_surface(
            X,
            Y,
            Z_top,
            cmap="viridis",
            linewidth=0,
            antialiased=True,
            alpha=0.95,
        )

        Z_bottom = np.ones_like(X) * (-half)

        ax.plot_surface(
            X,
            Y,
            Z_bottom,
            color="lightgray",
            linewidth=0,
            alpha=0.20,
        )

        ax.plot_surface(
            np.vstack([x, x]),
            np.vstack([np.ones_like(x) * -half, np.ones_like(x) * -half]),
            np.vstack([np.ones_like(x) * -half, Z_top[0, :]]),
            color="lightgray",
            alpha=0.35,
        )

        ax.plot_surface(
            np.vstack([x, x]),
            np.vstack([np.ones_like(x) * half, np.ones_like(x) * half]),
            np.vstack([np.ones_like(x) * -half, Z_top[-1, :]]),
            color="lightgray",
            alpha=0.35,
        )

        ax.plot_surface(
            np.vstack([np.ones_like(y) * -half, np.ones_like(y) * -half]),
            np.vstack([y, y]),
            np.vstack([np.ones_like(y) * -half, Z_top[:, 0]]),
            color="lightgray",
            alpha=0.35,
        )

        ax.plot_surface(
            np.vstack([np.ones_like(y) * half, np.ones_like(y) * half]),
            np.vstack([y, y]),
            np.vstack([np.ones_like(y) * -half, Z_top[:, -1]]),
            color="lightgray",
            alpha=0.35,
        )

        for i, (sx, sy) in enumerate(sensor_positions):
            ix = np.argmin(np.abs(x - sx))
            iy = np.argmin(np.abs(y - sy))
            sz = Z_top[iy, ix]

            ax.scatter(
                sx,
                sy,
                sz + 1.0,
                s=40,
                color="black",
            )

            ax.text(
                sx,
                sy,
                sz + 3.0,
                sensor_labels[i],
                ha="center",
                fontsize=8,
            )

        ix = np.argmin(np.abs(x - estimated_xy[0]))
        iy = np.argmin(np.abs(y - estimated_xy[1]))
        estimated_z = Z_top[iy, ix]

        ax.scatter(
            estimated_xy[0],
            estimated_xy[1],
            estimated_z + 2.0,
            s=100,
            color="red",
        )

        plt.draw()
        plt.pause(0.001)


    try:
        while running and plt.fignum_exists(fig.number):
            sensor_data = sensor_stream.get_data(num_samples=1)[0][1:]

            display_data = sensor_data - baseline

            draw_cube(display_data)

    except KeyboardInterrupt:
        print("Stopped.")

    finally:
        print("Closing visualiser...")

        plt.ioff()

        if plt.fignum_exists(fig.number):
            plt.close(fig)

        try:
            sensor_stream.pause_streaming()
            sensor_stream.join()
        except Exception as e:
        print("Visualiser closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="eFlesh cube deformation visualiser."
    )

    parser.add_argument(
        "-p",
        "--port",
        type=str,
        default="/dev/ttyACM0",
        help="port connected to the microcontroller",
    )

    parser.add_argument(
        "-s",
        "--scaling",
        type=float,
        default=70.0,
        help="larger value gives smaller deformation",
    )

    args = parser.parse_args()

    visualize(
        port=args.port,
        scaling=args.scaling,
    )
