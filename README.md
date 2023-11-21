# Process Uniaxial TDMS

## Overview
"Process Uniaxial TDMS" is a standalone Windows application that facilitates the processing of TDMS files generated from uniaxial tests. It provides a user-friendly graphical interface, allowing users to select input and output directories, convert TDMS files to CSV format, pick key data points, and perform optional stress-strain analysis to derive Young's Modulus and Poisson's Ratio.

## System Requirements
- Operating System: Windows 7 or later.
- Memory: At least 2 GB RAM (4 GB recommended).
- Storage: At least 100 MB free space for the application, plus additional space for data files.

## Installation
No installation is necessary. The application is distributed as a single executable file:

1. Download "Process Uniaxial TDMS.exe" from the [Releases](#) page.
2. Place the executable in your desired directory.
3. Run the application by double-clicking on the executable.

## Usage
Follow these steps to process your TDMS files:

1. **Select Input Directory**: Click "Browse Input Directory" to choose the folder containing your TDMS files.
2. **Select Output Directory**: Click "Browse Output Directory" to specify where the processed files and results will be stored.
3. **Process Files**: Click "Process Files" to start the conversion and analysis. The application will handle the rest.

### Configuration
Enter the machine stiffness correction factor (default 0.0023 mm/kN) in the provided input field if necessary.

## Output
The application outputs CSV files with key data points, a summary of results, and stress-strain analysis if selected.

## Troubleshooting
If the application does not start, ensure that your system meets the requirements and that you have the appropriate permissions to execute the program.

For file processing issues, confirm that the input directory contains valid TDMS files and that the output directory is not write-protected.

## Contributing
Contributions to the project are welcome! Please submit issues or pull requests through the GitHub repository.

## License
This project is licensed under the [MIT License](#) - see the LICENSE file for details.

