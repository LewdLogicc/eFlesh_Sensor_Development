import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load experimental data
data = pd.read_csv('eflesh_data.csv')

time = data['time_s'].to_numpy()
time = time - time[0]

# Assumed magnetometer coordinates (mm)
# These positions have NOT been verified.
sensor_positions = {
    'M0_S0': (10, 20),  # Left
    'M0_S1': (30, 20),  # Right
    'M0_S2': (20, 20),  # Centre
    'M0_S3': (20, 10),  # Bottom
    'M0_S4': (20, 30),  # Top
}

# Calculate baseline-corrected responses
responses = {}

for sensor in sensor_positions:

    bx = data[f'{sensor}_Bx'].to_numpy()
    by = data[f'{sensor}_By'].to_numpy()
    bz = data[f'{sensor}_Bz'].to_numpy()

    baseline = np.array([
        np.mean(bx[:10]),
        np.mean(by[:10]),
        np.mean(bz[:10])
    ])

    responses[sensor] = np.sqrt(
        (bx - baseline[0])**2 +
        (by - baseline[1])**2 +
        (bz - baseline[2])**2
    )

# Weighted centroid calculation
x_est = []
y_est = []

for i in range(len(time)):

    weights = np.array([
        responses[sensor][i]
        for sensor in sensor_positions
    ])

    coordinates = np.array(list(sensor_positions.values()))

    if np.sum(weights) > 0:

        centroid = np.average(
            coordinates,
            axis=0,
            weights=weights
        )

        x_est.append(centroid[0])
        y_est.append(centroid[1])

    else:
        x_est.append(np.nan)
        y_est.append(np.nan)

# Plot estimated position over time
plt.figure(figsize=(10, 5))

plt.plot(time, x_est, label='Estimated X')
plt.plot(time, y_est, label='Estimated Y')

plt.xlabel('Time (s)')
plt.ylabel('Estimated Position (mm)')
plt.title('Magnetic Response Weighted Centroid Localisation')
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig('contact_localisation_centroid.png', dpi=300)
plt.show()
