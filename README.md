# QuLab - Interest Rate Risk in the Banking Book (IRRBB) Simulation

<p align="center">
  <img src="https://www.quantuniversity.com/assets/img/logo5.jpg" alt="QuantUniversity Logo" width="150"/>
</p>

## Project Overview

**QuLab** is a Streamlit-based educational application designed to explore the concepts of Interest Rate Risk in the Banking Book (IRRBB), with a particular focus on the Economic Value of Equity (EVE). This interactive tool allows users to simulate the impact of various interest rate shocks on a bank's economic value by generating synthetic banking book portfolios, creating yield curves, calculating cash flows, and performing stress tests.

The application aims to provide a practical understanding of how changes in market interest rates can affect a bank's net worth and profitability, incorporating key regulatory concepts such as ΔEVE and Net Gap analysis.

### Key Concepts Explored:

*   **IRRBB (Interest Rate Risk in the Banking Book):** The risk to a bank's earnings and capital arising from adverse movements in interest rates.
*   **EVE (Economic Value of Equity):** Represents the present value of a bank's expected cash flows from its assets minus the present value of its expected cash flows from its liabilities. It's a measure of the bank's long-term economic net worth.
    $$ EVE_{\text{baseline}} = \sum_{i=1}^{N_A} PV(CF_{A,i}) - \sum_{j=1}^{N_L} PV(CF_{L,j}) $$
    Where:
    *   $N_A$ is the number of assets.
    *   $N_L$ is the number of liabilities.
    *   $PV(CF_{A,i})$ is the present value of the cash flows of asset $i$.
    *   $PV(CF_{L,j})$ is the present value of the cash flows of liability $j$.
*   **Present Value (PV) Calculation:** The value today of a future stream of cash flows.
    $$ PV(CF_t) = \frac{CF_t}{(1 + r_t)^{t}} $$
    or
    $$ PV = \sum_{k=1}^{M} \frac{CF_k}{(1 + r_{t_k})^{t_k}} $$
    Where:
    *   $CF_t$ is the cash flow at time t.
    *   $r_t$ is the discount rate for time t.
    *   $r_{t_k}$ is the discount rate for time $t_k$.
*   **ΔEVE (Change in Economic Value of Equity):** The shift in EVE under a defined interest rate shock scenario, relative to a baseline EVE. This is a critical metric used by regulators (e.g., Basel Committee on Banking Supervision) to assess IRRBB.
    $$ \Delta EVE = EVE_{\text{shocked}} - EVE_{\text{baseline}} $$
    $$ \Delta EVE (\% \text{ Tier 1 Capital}) = \frac{\Delta EVE}{\text{Tier 1 Capital}} \times 100\% $$
*   **Net Gap Analysis:** A simplified measure of interest rate risk exposure, representing the difference between interest rate sensitive assets and liabilities within defined time buckets. A positive gap indicates asset sensitivity, while a negative gap indicates liability sensitivity.
    $$ Net\ Gap_{\text{bucket } k} = \sum_{\text{assets in bucket } k} CF_{\text{in}} - \sum_{\text{liabilities in bucket } k} CF_{\text{out}} $$

---

## ✨ Features

QuLab offers the following key functionalities:

*   **📈 Portfolio Generation:**
    *   Generate a synthetic banking book portfolio with configurable numbers of instruments, Tier 1 Capital, and date ranges.
    *   Includes a mix of assets (Loans, Bonds, Mortgages) and liabilities (Deposits), as well as Swaps.
    *   Instruments feature diverse characteristics: Issue Date, Maturity Date, Amount, Rate Type (Fixed, Floating, Hybrid), Coupon Rate, Payment Frequency, and specific features (e.g., prepayment options for mortgages, NMD flags for deposits).
*   **📊 Discount Curve Management:**
    *   Generate a baseline discount (yield) curve based on market rates and adjustable liquidity spreads.
    *   Visualize the generated yield curve to understand its shape and rates across different tenors.
*   **💡 IRRBB Simulation & Analysis:**
    *   **Cash Flow Generation:** Automatically generate projected cash flows for each instrument in the portfolio (principal and interest payments).
    *   **Behavioral Assumptions:** Apply behavioral models for instruments like Mortgages (prepayment) and Non-Maturity Deposits (NMDs - behavioral maturity and beta).
    *   **Basel Bucketing:** Map cash flows into predefined Basel IRRBB time buckets for granular analysis.
    *   **Present Value Calculation:** Discount future cash flows using the generated yield curves to calculate the present value of assets and liabilities.
    *   **Interest Rate Shock Scenarios:** Apply standard Basel-defined interest rate shock scenarios (e.g., Parallel Up/Down, Steepener, Flattener, Short Rate Up/Down).
    *   **Dynamic Repricing:** Re-price floating rate instrument cash flows and adjust behavioral assumptions (e.g., prepayment rates) under different shock scenarios.
    *   **EVE & ΔEVE Calculation:** Compute the Economic Value of Equity (EVE) under baseline and shocked scenarios, and determine the change (ΔEVE).
    *   **Reporting:** Present ΔEVE results both in absolute terms and as a percentage of Tier 1 Capital, aligned with regulatory reporting standards.
    *   **Net Gap Analysis:** Calculate and visualize the Net Gap for the portfolio across Basel time buckets.
    *   **Interactive Visualizations:** Utilize Plotly for dynamic charts to visualize yield curves, ΔEVE impact, and Net Gap.

---

## 🚀 Getting Started

Follow these instructions to get QuLab up and running on your local machine.

### Prerequisites

*   Python 3.7+
*   `pip` (Python package installer)
*   `git` (for cloning the repository)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/QuLab.git
    cd QuLab
    ```
    *(Note: Replace `https://github.com/your-username/QuLab.git` with the actual repository URL if it's hosted.)*

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    *   **On Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required dependencies:**

    Create a `requirements.txt` file in the root directory (`QuLab/`) with the following content:

    ```
    streamlit==1.30.0
    pandas==2.1.4
    numpy==1.26.2
    scipy==1.11.4
    plotly==5.18.0
    python-dateutil==2.8.2
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```

---

## 💻 Usage

1.  **Run the Streamlit application:**

    Make sure your virtual environment is activated and you are in the `QuLab/` directory.

    ```bash
    streamlit run app.py
    ```

2.  **Access the Application:**

    The command above will open the QuLab application in your default web browser (usually at `http://localhost:8501`).

3.  **Navigate and Interact:**

    *   Use the **sidebar** on the left to navigate between different sections:
        *   **Portfolio Generation:** Start here to create your synthetic banking book. Adjust parameters like the number of instruments and Tier 1 Capital. Click "Generate Portfolio". The generated portfolio data will be saved in `st.session_state` for use in other sections.
        *   **Discount Curve:** (Assuming this page exists and is functional) View and potentially modify the baseline yield curve.
        *   **IRRBB Simulation:** (Assuming this page exists and is functional) Conduct IRRBB stress tests, apply shock scenarios, and analyze ΔEVE and Net Gap results.

    *   Adjust input parameters using sliders, number inputs, and date pickers as provided in each section.
    *   The application uses Streamlit's caching (`@st.cache_data`) for performance, so calculations are optimized.

---

## 📁 Project Structure

```
QuLab/
├── app.py                      # Main Streamlit application entry point
├── requirements.txt            # Python dependencies
└── application_pages/          # Directory for individual application pages and utility functions
    ├── __init__.py             # Makes application_pages a Python package
    ├── portfolio_generation.py # Logic and UI for generating synthetic portfolios
    ├── discount_curve.py       # (Assumed) Logic and UI for managing discount curves
    ├── irrbb_simulation.py     # (Assumed) Logic and UI for running IRRBB simulations
    └── utils.py                # Shared utility functions, constants, and core financial calculations
```

---

## 🛠️ Technology Stack

*   **Application Framework:** [Streamlit](https://streamlit.io/)
*   **Programming Language:** Python
*   **Data Manipulation:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
*   **Scientific Computing & Interpolation:** [SciPy](https://scipy.org/)
*   **Date/Time Handling:** `datetime` (standard library), [python-dateutil](https://dateutil.readthedocs.io/en/stable/)
*   **Charting Library:** [Plotly](https://plotly.com/python/)
*   **Unique ID Generation:** `uuid` (standard library)

---

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements, new features, or bug fixes, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add new feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

```
MIT License

Copyright (c) 2024 Your Name or Organization

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Contact

For any questions or inquiries, please reach out:

*   **QuantUniversity:** [www.quantuniversity.com](https://www.quantuniversity.com/)
*   **Project Maintainer:** [Your Name/Email/LinkedIn] (Optional)

---
