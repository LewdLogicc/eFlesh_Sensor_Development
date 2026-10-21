import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
import shutil

experiment_name = input('Enter experiment name: ').strip()

if not experiment_name:
    experiment_name = 'experiment'

# Make experiment name safe for folder names
experiment_name = ''.join(
    c if c.isalnum() or c in '-_' else '_'
    for c in experiment_name
)

timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')

experiment_folder = (
    Path.home()
    / 'eflesh_ws'
    / 'experimental_data'
    / f'{experiment_name}_{timestamp}'
)

experiment_folder.mkdir(parents=True, exist_ok=False)

# CSV location
csv_file = Path(__file__).resolve().parent / 'eflesh_data.csv'

# Copy CSV 
shutil.copy2(
    csv_file,
    experiment_folder / 'eflesh_data.csv'
)

print(f'\nExperiment folder created: {experiment_folder}')
print('CSV saved successfully.')

data = pd.read_csv(csv_file)

# Time axis
time = data['time_s'] - data['time_s'].iloc[0]


# Figure 1 - Individual magnetometer response
sensor = 'M0_S0'

bx = data[f'{sensor}_Bx']
by = data[f'{sensor}_By']
bz = data[f'{sensor}_Bz']

plt.figure(figsize=(10, 5))

plt.plot(time, bx, label='Bx')
plt.plot(time, by, label='By')
plt.plot(time, bz, label='Bz')

plt.xlabel('Time (s)')
plt.ylabel('Magnetic Flux Density (µT)')
#plt.title('Single Magnetometer Baseline Magnetic Flux Density')
plt.title('Single Magnetometer Magnetic Flux Density During Contact and Release')
#plt.title('Magnetic Flux Density Contact Recovery')
#plt.title('Magnetic Flux Density Contact Recovery')
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    experiment_folder / 'magnetic_response_individual.png',
    dpi=300
)

plt.show()

# Calculate baseline-corrected magnetic response
responses = {}

for module in range(3):
    for sensor_num in range(5):

        sensor = f'M{module}_S{sensor_num}'

        bx = data[f'{sensor}_Bx'].to_numpy()
        by = data[f'{sensor}_By'].to_numpy()
        bz = data[f'{sensor}_Bz'].to_numpy()

        # Baseline from first 10 samples
        baseline = np.array([
            np.mean(bx[:10]),
            np.mean(by[:10]),
            np.mean(bz[:10])
        ])

        # Calculate magnetic field change
        delta_b = np.sqrt(
            (bx - baseline[0])**2 +
            (by - baseline[1])**2 +
            (bz - baseline[2])**2
        )

        responses[sensor] = delta_b


# Figure 2 - Five largest responses
top_sensors = sorted(
    responses,
    key=lambda s: np.max(responses[s]),
    reverse=True
)[:5]

plt.figure(figsize=(10, 5))

for sensor in top_sensors:
    plt.plot(
        time,
        responses[sensor],
        label=sensor
    )

plt.xlabel('Time (s)')
plt.ylabel('Change in Magnetic Flux Density (µT)')
#plt.title('Multiplexed Array Baseline Magnetic Flux Density Variation')
#plt.title('Multiplexed Array Magnetic Flux Density Contact Recovery')
plt.title('Single Sensor Magnetic Flux Density Contact Localisation')
#plt.title('Multiplexed Array Magnetic Flux Density Contact Recovery')
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    experiment_folder / 'magnetic_response_array.png',
    dpi=300
)

plt.show()


# Figures 3-5 - Individual module responses
for module in range(3):

    plt.figure(figsize=(10, 5))

    for sensor_num in range(5):

        sensor = f'M{module}_S{sensor_num}'

        plt.plot(
            time,
            responses[sensor],
            label=sensor
        )

    plt.xlabel('Time (s)')
    plt.ylabel('Change in Magnetic Flux Density (µT)')
    #plt.title(f'Module M{module} Magnetic Flux Density Variation')
    plt.title(f'Module M{module} Magnetic Flux Density Contact Recovery')
    #plt.title(f'Module M{module} Magnetic Flux Density Contact Recovery')
    #plt.title(f'Module M{module} Magnetic Flux Density Contact Recovery')
    #plt.title(f'Module M{module} Magnetic Flux Density Contact Recovery')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        experiment_folder / f'magnetic_response_M{module}.png',
        dpi=300
    )

    plt.show()


# Figure 6 - Maximum magnetic response per module
plt.figure(figsize=(10, 5))

for module in range(3):

    module_sensors = [
        responses[f'M{module}_S{s}']
        for s in range(5)
    ]

    # Maximum response among five sensors in the module
    module_response = np.max(
        np.array(module_sensors),
        axis=0
    )

    plt.plot(
        time,
        module_response,
        label=f'M{module}'
    )

plt.xlabel('Time (s)')
plt.ylabel('Change in Magnetic Flux Density (µT)')
#plt.title('Combined Magnetic Flux Density Variation')
plt.title('Combined Magnetic Flux Density Contact Recovery')
#plt.title('Combined Baseline Magnetic Flux Density Contact Recovery')
#plt.title('Combined Baseline Magnetic Flux Density Contact Recovery')
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    experiment_folder / 'magnetic_response_modules.png',
    dpi=300
)

plt.show()



print('\nGraphs saved successfully.')
print('Top five sensors:', top_sensors)
print(f'\nAll experimental data saved to:\n{experiment_folder}')