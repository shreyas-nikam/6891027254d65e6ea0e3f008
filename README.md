# QuLab: Comprehensive Interest Rate Risk in the Banking Book (IRRBB) Engine

## Project Description

**QuLab** is a Streamlit-powered analytical application designed to provide a comprehensive framework for assessing Interest Rate Risk in the Banking Book (IRRBB). Developed as a lab project, this application enables users to simulate a synthetic banking book portfolio, generate detailed cash flows, apply various Basel interest rate shock scenarios, and quantify the resulting change in Economic Value of Equity ($\Delta EVE$).

The application implements a full-revaluation approach, allowing for a deep understanding of how interest rate movements impact a bank's balance sheet from an EVE perspective. It aims to bridge theoretical concepts of IRRBB with practical application, offering an intuitive interface for risk analysts, finance professionals, and students to explore complex financial risk models.

### Learning Goals

Upon using this application, you will be able to:
*   Assemble a banking-book positions dataset that captures interest-sensitive assets, liabilities, and (optionally) simple hedges.
*   Generate synthetic cash-flow data for those positions, respecting product features and behavioural assumptions.
*   Build a full-revaluation IRRBB engine that computes baseline present values, allocates cash flows into regulatory time buckets, and estimates $\Delta EVE$ under the Basel six-scenario shock set.
*   Report $\Delta EVE$ as a percentage of Tier 1 capital and interpret the risk signal of each scenario.

### Mathematical Foundations for EVE

The Present Value (PV) of a series of cash flows is the sum of the present values of each individual cash flow. For a single cash flow $CF_t$ received at time $t$, discounted at a rate $r_t$:
$$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$
For a series of cash flows $CF_1, CF_2, \ldots, CF_M$ occurring at times $t_1, t_2, \ldots, t_M$:
$$ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $$
For EVE calculation, the cash flows will be discounted using a risk-free yield curve plus an appropriate liquidity spread; commercial margins are excluded.

EVE is defined as the present value of all banking book assets minus the present value of all banking book liabilities and off-balance sheet items:
$$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$

$\Delta EVE$ measures the change in a bank's EVE due to an interest rate shock:
$$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$

$\Delta EVE$ will be reported as a percentage of Tier 1 capital, allowing for a standardized interpretation of the risk signal:
$$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$

The net gap for each time bucket represents the difference between total cash inflows (from assets) and total cash outflows (from liabilities and derivatives) within that bucket:
$$ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $$

## Features

*   **Synthetic Portfolio Generation**: Create a customizable synthetic banking book portfolio with various instruments (Loans, Deposits, Bonds), rate types (fixed/floating), and maturity profiles.
*   **Dynamic Cash Flow Projection**: Project future cash flows for each instrument based on its contractual terms.
*   **Behavioral Modeling**: Incorporate behavioral assumptions for specific products:
    *   **Mortgage Prepayment**: Adjusts loan principal cash flows based on user-defined prepayment rates.
    *   **Non-Maturity Deposits (NMDs)**: Models the stable portion of NMDs with an assumed behavioral maturity.
*   **Baseline Discount Curve Construction**: Build a baseline yield curve by interpolating market rates and applying a user-defined liquidity spread.
*   **Net Gap Analysis**: Map projected cash flows into predefined Basel regulatory time buckets to compute the net interest rate gap.
*   **Economic Value of Equity (EVE) Calculation**: Compute the baseline EVE for the banking book portfolio.
*   **Basel Interest Rate Shock Scenarios**: Simulate the impact of six standardized Basel II/III interest rate shock scenarios (Parallel Up/Down, Steepener, Flattener, Short-Up, Short-Down).
*   **$\Delta EVE$ Quantification**: Calculate the change in EVE under each shock scenario relative to the baseline.
*   **Tier 1 Capital Reporting**: Report $\Delta EVE$ as a percentage of the bank's Tier 1 capital for standardized risk assessment.
*   **Interactive Visualizations**: Visualize $\Delta EVE$ across scenarios using interactive Plotly charts.
*   **Data Export**: Download generated portfolio data, cash flow reports, and simulation results in various formats (CSV, Parquet, Pickle).

## Getting Started

Follow these instructions to set up and run the QuLab application on your local machine.

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/<your-username>/QuLab.git
    cd QuLab
    ```
    (Replace `<your-username>` with your actual GitHub username or the repository's path.)

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required dependencies:**
    Create a `requirements.txt` file in the root directory of your project with the following content:
    ```
    streamlit
    pandas
    numpy
    python-dateutil
    scipy
    plotly
    openpyxl # For potential Excel operations, though not explicitly used for output in provided code
    pyarrow # For parquet support
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the Streamlit application:**
    Ensure your virtual environment is active and you are in the project's root directory (where `app.py` is located).
    ```bash
    streamlit run app.py
    ```
    This command will open the application in your default web browser.

2.  **Navigate the Application:**
    The application is structured into three main pages, accessible via the sidebar on the left:
    *   **Portfolio Generation**:
        *   Input parameters like `Number of Instruments`, `Tier 1 Capital`, `Portfolio Start Date`, and `Portfolio End Date`.
        *   Clicking `Generate` (implicitly, as it regenerates on parameter change) will create a synthetic banking book portfolio.
        *   You can view a sample of the generated portfolio and download the full dataset.
    *   **Cash Flow & Gap Analysis**:
        *   Adjust `Model Parameters` such as `Liquidity Spread`, `Mortgage Prepayment Rate`, `NMD Beta`, and `NMD Behavioral Maturity`.
        *   Click `Run Cash Flow & Gap Analysis` to project cash flows, apply behavioral assumptions, create the baseline discount curve, calculate baseline EVE, and generate the Net Gap table.
        *   Review the generated discount curve, cash flow samples, and the Net Gap table.
    *   **IRRBB Simulation Results**:
        *   Once the previous steps are completed, click `Run IRRBB Simulation`.
        *   The application will run all six Basel shock scenarios, recalculate EVE under each shock, and compute $\Delta EVE$.
        *   View the `Delta EVE Report` showing absolute and percentage changes relative to Tier 1 Capital, along with a bar chart visualization.
        *   Download the full model artifact (a pickle file containing key results) for offline analysis or auditing.

## Project Structure

```
QuLab/
├── application_pages/
│   ├── __init__.py                # Makes application_pages a Python package
│   ├── irrbb_core_functions.py    # Core business logic: portfolio generation, CF, PV, EVE, shocking, etc.
│   ├── page1.py                   # Streamlit UI for Portfolio Generation
│   ├── page2.py                   # Streamlit UI for Cash Flow & Gap Analysis
│   └── page3.py                   # Streamlit UI for IRRBB Simulation Results
├── app.py                         # Main Streamlit application entry point, global constants, navigation
└── requirements.txt               # List of Python dependencies
```

## Technology Stack

*   **Core Application Framework**: [Streamlit](https://streamlit.io/)
*   **Programming Language**: Python
*   **Data Manipulation**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
*   **Date & Time Utilities**: [datetime](https://docs.python.org/3/library/datetime.html), [dateutil](https://dateutil.readthedocs.io/en/stable/)
*   **Numerical Operations & Interpolation**: [SciPy](https://scipy.org/)
*   **Interactive Visualization**: [Plotly Express](https://plotly.com/python/plotly-express/)
*   **Data Serialization**: [Pickle](https://docs.python.org/3/library/pickle.html)
*   **Data Storage Formats**: CSV, Parquet

## Contributing

Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -m 'Add new feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a Pull Request.

Please ensure your code adheres to good practices, is well-commented, and includes appropriate tests if applicable.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please open an issue in the GitHub repository or contact:

*   **Author**: [Your Name/Organization Name]
*   **GitHub**: [Your GitHub Profile/Organization Link]