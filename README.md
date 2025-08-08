# QuLab: Interest Rate Risk in the Banking Book (IRRBB) Simulation

## Project Overview

**QuLab** is an interactive Streamlit application developed as a lab project for exploring the intricacies of Interest Rate Risk in the Banking Book (IRRBB), with a specific focus on the Economic Value of Equity (EVE) framework. The application provides a dynamic simulation environment where users can generate synthetic banking portfolios, project cash flows under various behavioral assumptions, and assess the impact of interest rate shocks on a bank's economic value.

This tool aims to provide a clear, visual, and interactive understanding of how interest rate movements can affect a bank's long-term economic value, supporting risk management and regulatory insights in the context of Basel III guidelines.

### What is IRRBB?

IRRBB refers to the current or prospective risk to a bank's capital and earnings arising from adverse movements in interest rates that affect the bank's banking book positions. These positions are held with the intention of being held to maturity or for liquidity purposes, as opposed to trading book positions which are held for short-term profit from price movements.

### Economic Value of Equity (EVE)

EVE is a key metric in IRRBB, representing the present value of the bank's expected future cash flows from its assets, liabilities, and off-balance sheet items. It provides a static, long-term view of risk, capturing the impact of interest rate changes on the underlying value of the bank.

Mathematically, the baseline EVE is defined as:

$$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$

Where:
- $N_A$ is the number of assets.
- $N_L$ is the number of liabilities.
- $PV(CF_{A,i})$ is the Present Value of cash flows from asset $i$.
- $PV(CF_{L,j})$ is the Present Value of cash flows from liability $j$.

The application also calculates the change in Economic Value of Equity ($\Delta EVE$) under various stress scenarios and reports it as a percentage of Tier 1 Capital, a crucial metric for regulatory compliance.

## Features

*   **Synthetic Banking Portfolio Generation**: Dynamically create a customizable portfolio of interest-sensitive assets (e.g., Mortgages, Corporate Loans, Government Bonds) and liabilities (e.g., Non-Maturity Deposits, Fixed Deposits).
*   **Cash Flow Projection**: Project future cash flows for each instrument, integrating key behavioral assumptions such as:
    *   **Mortgage Prepayment Models**: Account for the early repayment of mortgage loans.
    *   **Non-Maturity Deposit (NMD) Beta**: Model the sensitivity of NMD rates to market interest rate changes and assign an effective duration for these non-contractual liabilities.
*   **Baseline EVE Calculation**: Compute the initial Economic Value of Equity for the generated portfolio.
*   **Net Gap Analysis**: Visualize repricing and maturity mismatches by summarizing net cash flows across predefined Basel regulatory time buckets.
*   **Interest Rate Shock Scenarios**: Apply the six prescribed Basel interest rate shock scenarios to the generated portfolio:
    *   Parallel Up
    *   Parallel Down
    *   Steepener (short rates down, long rates up)
    *   Flattener (short rates up, long rates down)
    *   Short-Term Rate Up
    *   Short-Term Rate Down
*   **Delta EVE Reporting**: Calculate and visualize the change in EVE ($\Delta EVE$) for each shock scenario, expressed as a percentage of Tier 1 Capital, for comprehensive risk assessment.
*   **Interactive Controls**: Adjust various parameters like the number of instruments, Tier 1 Capital, portfolio dates, liquidity spreads, and behavioral assumptions through a user-friendly sidebar.

## Getting Started

Follow these instructions to set up and run the QuLab application on your local machine.

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/QuLab-IRRBB-Simulation.git
    cd QuLab-IRRBB-Simulation
    ```
    *(Note: Replace `https://github.com/your-username/QuLab-IRRBB-Simulation.git` with the actual repository URL if this project is hosted.)*

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    Create a `requirements.txt` file in the root directory of your project with the following content:
    ```
    streamlit
    pandas
    numpy
    scipy
    plotly
    python-dateutil
    ```
    Then, install them:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the Streamlit application:**
    Ensure your virtual environment is activated and you are in the root directory of the `QuLab-IRRBB-Simulation` project (where `app.py` is located).
    ```bash
    streamlit run app.py
    ```
    This command will open the application in your default web browser.

2.  **Navigate the Application:**
    *   The application starts on the "Portfolio Generation" (Page 1) tab, providing an introduction to the lab and instructions on how to use the app.
    *   Use the sidebar on the left to navigate to "IRRBB Analysis" (Page 2) to start your simulation.

3.  **Perform a Simulation:**
    *   On the "IRRBB Analysis" page, you will find various input widgets in the sidebar.
    *   **Adjust Parameters**:
        *   **Portfolio Generation Parameters**: Define the number of synthetic instruments, Tier 1 Capital, and the date range for portfolio generation.
        *   **Discount Curve Parameters**: Set the liquidity spread to be applied to the baseline risk-free curve.
        *   **Behavioral Assumption Parameters**: Configure annual mortgage prepayment rates, NMD Beta, NMD behavioral maturity, and a factor to adjust behavioral rates under shock.
    *   **Run Simulation**: Click the "Run IRRBB Simulation" button in the sidebar. The application will then perform all calculations, generate the portfolio, project cash flows, calculate EVE, run stress scenarios, and display the results in the main content area.
    *   **Analyze Results**: Review the generated tables and charts for:
        *   Initial Portfolio Overview
        *   Baseline Discount Curve
        *   Baseline Economic Value of Equity (EVE)
        *   Net Gap Analysis by Basel Time Bucket
        *   Delta EVE Report (% of Tier 1 Capital) for each shock scenario.

4.  **Explore the "About" page:** Learn more about the application's purpose and technology stack.

## Project Structure

```
QuLab-IRRBB-Simulation/
├── app.py                      # Main Streamlit application entry point and navigation
├── application_pages/          # Directory for individual application pages
│   ├── page1.py                # Introduction and guidance for portfolio generation
│   ├── page2.py                # Core IRRBB calculation engine and EVE simulation UI
│   └── page3.py                # About section for the application
└── requirements.txt            # List of Python dependencies
└── README.md                   # Project README file
```

## Technology Stack

*   **Streamlit**: For building the interactive web user interface.
*   **Pandas**: For efficient data manipulation and analysis, primarily with DataFrames.
*   **NumPy**: For numerical operations, especially for array manipulations and mathematical calculations.
*   **SciPy**: Specifically, `scipy.interpolate` is used for interpolating interest rates to build continuous discount curves.
*   **Plotly**: For creating interactive and dynamic data visualizations, including bar charts for Net Gap and Delta EVE.
*   **Python `datetime` & `dateutil`**: For robust date and time calculations, crucial for handling maturities and cash flow schedules.
*   **Python `uuid`**: For generating unique identifiers for financial instruments.
*   **Python `random`**: For generating synthetic portfolio data.

## Contributing

Contributions are welcome! If you have suggestions for improvements, new features, or bug fixes, please feel free to:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/AmazingFeature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
5.  Push to the branch (`git push origin feature/AmazingFeature`).
6.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details (if applicable, create a `LICENSE` file in your repository if you intend to formally license it).

## Contact

For more information about Quant University labs and courses, please visit [www.quantuniversity.com](https://www.quantuniversity.com).
