rates_for_interp_x = [0] + rates_df["Months_to_Maturity"].tolist()
    rates_for_interp_y = [rates_df["rate_decimal"].iloc[0]] + rates_df["rate_decimal"].tolist()

    f_interp = interp1d(rates_for_interp_x, rates_for_interp_y, kind="linear", fill_value="extrapolate")

    # Generate rates for each month from 0 up to the maximum tenor
    all_months = np.arange(0, max_months + 1)
    interpolated_rates = f_interp(all_months)

    baseline_curve_df = pd.DataFrame({
        "Months_to_Maturity": all_months,
        "Rate": interpolated_rates,
    })
    baseline_curve_df["Valuation_Date"] = valuation_date
    return baseline_curve_df

@st.cache_data
def calculate_cashflows_for_instrument(instrument_data, baseline_curve):
    instrument_id = instrument_data["Instrument_ID"]
    issue_date = instrument_data["Issue_Date"]
    maturity_date = instrument_data["Maturity_Date"]
    amount = instrument_data["Amount"]
    rate_type = instrument_data["Rate_Type"]
    coupon_rate = instrument_data["Coupon_Rate"]
    payment_frequency = instrument_data["Payment_Frequency"]
    is_asset = instrument_data["Is_Asset"]
    specific_features = instrument_data["Specific_Features"]

    cashflows = []

    # Determine payment frequency in months
    if payment_frequency == "Monthly":
        freq_months = 1
    elif payment_frequency == "Quarterly":
        freq_months = 3
    elif payment_frequency == "Semi-Annually":
        freq_months = 6
    elif payment_frequency == "Annually":
        freq_months = 12
    else:
        freq_months = 12 # Default

    current_date = issue_date
    while current_date <= maturity_date:
        if current_date > issue_date: # Don't count initial funding as a coupon payment
            # Calculate period interest
            # For simplicity, assuming simple interest for the period, then discounted
            # More complex models would use exact day count conventions
            if rate_type == "Fixed":
                interest_payment = amount * coupon_rate * (freq_months / 12)
            elif rate_type == "Floating":
                # For initial cash flow generation, we can use the baseline rate at that tenor
                # This will be re-priced under shock scenarios
                months_to_maturity_at_payment = (current_date - baseline_curve["Valuation_Date"].iloc[0]).days / 30.44 # Approx months
                months_to_maturity_at_payment = max(0, int(round(months_to_maturity_at_payment)))
                # Find closest tenor rate, or interpolate
                if months_to_maturity_at_payment <= baseline_curve["Months_to_Maturity"].max():
                    current_market_rate = baseline_curve[baseline_curve["Months_to_Maturity"] == months_to_maturity_at_payment]["Rate"].iloc[0]
                else:
                    # Extrapolate or use last rate if beyond known curve - simplified
                    current_market_rate = baseline_curve["Rate"].iloc[-1]
                interest_payment = amount * current_market_rate * (freq_months / 12)
            elif rate_type == "Hybrid" and instrument_type == "Swap":
                # For swaps, we'll simplify and assume a net cash flow for now
                # A full swap model would track fixed and floating legs separately
                # Here, we'll treat it as a fixed cash flow for baseline, and adjust floating later
                interest_payment = amount * coupon_rate * (freq_months / 12) # Fixed leg equivalent
                # Add floating spread if applicable for the floating leg component
                if "floating_spread" in specific_features:
                    interest_payment += amount * specific_features["floating_spread"] * (freq_months / 12)
            else:
                interest_payment = 0 # For NMDs, etc., handled by behavioral model

            cashflows.append({
                "Instrument_ID": instrument_id,
                "Cashflow_Date": current_date,
                "Cashflow_Amount": interest_payment if is_asset else -interest_payment,
                "Type": "Interest"
            })

        current_date += relativedelta(months=freq_months)

    # Add principal repayment at maturity
    if amount > 0:
        cashflows.append({
            "Instrument_ID": instrument_id,
            "Cashflow_Date": maturity_date,
            "Cashflow_Amount": amount if is_asset else -amount,
            "Type": "Principal"
        })

    return pd.DataFrame(cashflows)

@st.cache_data
def apply_behavioral_assumptions(cashflow_df, behavioral_flag, prepayment_rate_annual, nmd_beta, nmd_behavioral_maturity_years):
    if cashflow_df.empty: return cashflow_df

    modified_cashflow_df = cashflow_df.copy()

    # Mortgage Prepayment
    if behavioral_flag == "Mortgage" and "Principal" in modified_cashflow_df["Type"].values:
        principal_cf = modified_cashflow_df[modified_cashflow_df["Type"] == "Principal"].copy()
        if not principal_cf.empty:
            # Simplistic prepayment: apply annual rate proportionally to remaining principal
            # This is a highly simplified model. Real prepayment models are complex (PSA, CPR, etc.)
            # For demonstration, we'll reduce the final principal by a factor
            # and distribute a portion earlier.
            final_principal_idx = principal_cf["Cashflow_Date"].idxmax()
            original_final_principal = principal_cf.loc[final_principal_idx, "Cashflow_Amount"]

            # Distribute a portion of original final principal as prepayment
            prepayment_amount = abs(original_final_principal) * prepayment_rate_annual

            # Reduce original final principal
            modified_cashflow_df.loc[final_principal_idx, "Cashflow_Amount"] -= np.sign(original_final_principal) * prepayment_amount

            # Add a prepayment cashflow earlier (e.g., at a fixed point or spread)
            # For simplicity, let's add it 1 year before maturity or halfway
            prepayment_date = modified_cashflow_df.loc[final_principal_idx, "Cashflow_Date"] - relativedelta(years=1)
            if prepayment_date < modified_cashflow_df["Cashflow_Date"].min():
                prepayment_date = modified_cashflow_df["Cashflow_Date"].min() # Ensure not before start

            # Add a new row for prepayment
            new_row = {
                "Instrument_ID": modified_cashflow_df["Instrument_ID"].iloc[0],
                "Cashflow_Date": prepayment_date,
                "Cashflow_Amount": np.sign(original_final_principal) * prepayment_amount,
                "Type": "Prepayment"
            }
            modified_cashflow_df = pd.concat([modified_cashflow_df, pd.DataFrame([new_row])], ignore_index=True)
            modified_cashflow_df = modified_cashflow_df.sort_values(by="Cashflow_Date").reset_index(drop=True)

    # Non-Maturity Deposit (NMD) Behavioral Maturity
    elif behavioral_flag == "NMD":
        # For NMDs, usually, the contractual maturity is "on demand".
        # Behavioral models assign an effective maturity. This means cashflows
        # that are contractually very short-term (e.g., daily) are treated as longer.
        # We will assume here that the NMD "principal" cashflow is shifted
        # from its contractual (e.g., immediate) maturity to the behavioral maturity.
        # This is a simplification; a full NMD model would use decay curves.

        # Find the original principal cashflow (assuming one for simplicity)
        principal_cf = modified_cashflow_df[modified_cashflow_df["Type"] == "Principal"]
        if not principal_cf.empty:
            original_principal_idx = principal_cf["Cashflow_Date"].idxmax()
            original_principal_amount = principal_cf.loc[original_principal_idx, "Cashflow_Amount"]
            original_maturity_date = principal_cf.loc[original_principal_idx, "Cashflow_Date"]

            # Calculate behavioral maturity date from valuation date (assuming initial valuation)
            valuation_date_for_nmd = min(modified_cashflow_df["Cashflow_Date"]) # Or explicit valuation date
            behavioral_maturity_date = valuation_date_for_nmd + relativedelta(years=nmd_behavioral_maturity_years)

            # Update the principal cashflow date
            modified_cashflow_df.loc[original_principal_idx, "Cashflow_Date"] = behavioral_maturity_date

            # Adjust interest payments using NMD Beta - Simplistic
            # This implies NMD rates move with market rates but less than 1:1
            # The impact of beta is more often on the rate used, rather than directly on existing cashflows.
            # For simplicity here, we'll represent it as a slight adjustment to interest cashflows.
            # In a full model, NMD beta is used in generating the assumed interest rate paid on NMDs.
            # We'll apply it during PV calculation by adjusting the effective discount rate or cashflow amount.
            # For now, this function focuses on maturity shifting.
            pass # NMD Beta effect is primarily in valuation/shock application

    return modified_cashflow_df.sort_values(by="Cashflow_Date").reset_index(drop=True)

@st.cache_data
def map_cashflows_to_basel_buckets(cashflow_df, valuation_date, basel_bucket_definitions):
    if cashflow_df.empty: return pd.DataFrame()

    bucketed_data = []

    # Ensure valuation_date is a datetime object
    if isinstance(valuation_date, date) and not isinstance(valuation_date, datetime):
        valuation_date = datetime.combine(valuation_date, datetime.min.time())

    for _, row in cashflow_df.iterrows():
        cf_date = row["Cashflow_Date"]
        cf_amount = row["Cashflow_Amount"]

        # Calculate months from valuation date to cashflow date
        if cf_date < valuation_date:
            months_to_cf = 0 # Already past valuation date, should ideally not have future CFs here
        else:
            # Calculate approximate months difference
            delta_years = (cf_date - valuation_date).days / 365.25
            months_to_cf = delta_years * 12

        bucket_assigned = "20Y+"
        for bucket_def in basel_bucket_definitions:
            min_m = bucket_def["min_months"]
            max_m = bucket_def["max_months"]

            if min_m <= months_to_cf < max_m:
                bucket_assigned = bucket_def["bucket"]
                break
        
        bucketed_data.append({
            "Instrument_ID": row["Instrument_ID"],
            "Cashflow_Date": cf_date,
            "Cashflow_Amount": cf_amount,
            "Bucket": bucket_assigned,
            "Is_Asset_Cashflow": cf_amount > 0 # Positive for assets, negative for liabilities
        })

    return pd.DataFrame(bucketed_data)

@st.cache_data
def calculate_present_value_for_cashflows(cashflow_df, discount_curve, valuation_date):
    if cashflow_df.empty: return 0.0

    total_pv = 0.0

    # Ensure valuation_date is a datetime object for comparison
    if isinstance(valuation_date, date) and not isinstance(valuation_date, datetime):
        valuation_date = datetime.combine(valuation_date, datetime.min.time())

    # Create a mapping from Months_to_Maturity to Rate for quick lookup
    rate_lookup = pd.Series(discount_curve["Rate"].values, index=discount_curve["Months_to_Maturity"]).to_dict()

    for _, row in cashflow_df.iterrows():
        cf_date = row["Cashflow_Date"]
        cf_amount = row["Cashflow_Amount"]

        if cf_date < valuation_date:
            # Cashflows already occurred, not part of future PV
            continue

        # Calculate time in years from valuation date
        time_delta_days = (cf_date - valuation_date).days
        time_in_years = time_delta_days / 365.25
        months_to_cf = round(time_in_years * 12)

        # Get the appropriate discount rate
        # Find the closest tenor rate available in the discount curve
        if months_to_cf in rate_lookup:
            r_t = rate_lookup[months_to_cf]
        else:
            # Interpolate if exact month is not found, or use nearest if outside range
            # For simplicity, let's find the closest available tenor.
            available_months = np.array(list(rate_lookup.keys()))
            if len(available_months) == 0: # Should not happen if curve is properly generated
                r_t = 0.0 # Or raise error
            elif months_to_cf < available_months.min():
                r_t = rate_lookup[available_months.min()]
            elif months_to_cf > available_months.max():
                r_t = rate_lookup[available_months.max()]
            else:
                # Simple linear interpolation between nearest points
                # More robust interpolation (e.g., spline) should be used for production
                lower_month = available_months[available_months <= months_to_cf].max()
                upper_month = available_months[available_months >= months_to_cf].min()

                if lower_month == upper_month: # Exact match for month
                    r_t = rate_lookup[lower_month]
                else:
                    rate_lower = rate_lookup[lower_month]
                    rate_upper = rate_lookup[upper_month]
                    r_t = rate_lower + (rate_upper - rate_lower) * (months_to_cf - lower_month) / (upper_month - lower_month)

        # Avoid division by zero or negative rates leading to very large PV
        if 1 + r_t <= 0:
            discount_factor = 0 # Or handle as error/infinite
        else:
            discount_factor = 1 / ((1 + r_t) ** time_in_years)

        total_pv += cf_amount * discount_factor

    return total_pv

@st.cache_data
def calculate_eve(pv_assets, pv_liabilities):
    return pv_assets - pv_liabilities

@st.cache_data
def calculate_net_gap(bucketed_cashflow_df):
    if bucketed_cashflow_df.empty: return pd.DataFrame()

    # Group by bucket and sum inflows (assets) and outflows (liabilities)
    inflows = bucketed_cashflow_df[bucketed_cashflow_df["Is_Asset_Cashflow"]].groupby("Bucket")["Cashflow_Amount"].sum().rename("Total_Inflows")
    outflows = bucketed_cashflow_df[~bucketed_cashflow_df["Is_Asset_Cashflow"]].groupby("Bucket")["Cashflow_Amount"].sum().rename("Total_Outflows")

    net_gap_df = pd.concat([inflows, outflows], axis=1).fillna(0)

    # Calculate Net Gap
    net_gap_df["Net_Gap"] = net_gap_df["Total_Inflows"] + net_gap_df["Total_Outflows"] # outflows are negative, so add them

    # Ensure all Basel buckets are present, even if no cash flows
    all_buckets = [b["bucket"] for b in basel_bucket_definitions_list]
    net_gap_df = net_gap_df.reindex(all_buckets, fill_value=0)

    return net_gap_df.reset_index().rename(columns={"index": "Bucket"})

@st.cache_data
def generate_basel_shocked_curve(baseline_curve, scenario_type, shock_magnitude_bps_short, shock_magnitude_bps_long):
    shocked_curve = baseline_curve.copy()
    shock_magnitude_short = shock_magnitude_bps_short / 10000.0 # Convert bps to decimal
    shock_magnitude_long = shock_magnitude_bps_long / 10000.0

    # Define short and long term boundaries in months
    # Basel often defines short-term as <= 1 year, long-term as > 1 year
    short_term_threshold_months = 12

    # Apply shock based on scenario type
    if scenario_type in ["Parallel Up", "Parallel Down"]:
        shocked_curve["Rate"] = baseline_curve["Rate"] + shock_magnitude_short # Same shock for all tenors
    elif scenario_type == "Steepener":
        # Short rates down, long rates up
        shocked_curve["Rate"] = baseline_curve["Rate"].apply(
            lambda r, months: r + (shock_magnitude_long if months > short_term_threshold_months else shock_magnitude_short),
            months=baseline_curve["Months_to_Maturity"]
        )
    elif scenario_type == "Flattener":
        # Short rates up, long rates down
        shocked_curve["Rate"] = baseline_curve["Rate"].apply(
            lambda r, months: r + (shock_magnitude_short if months <= short_term_threshold_months else shock_magnitude_long),
            months=baseline_curve["Months_to_Maturity"]
        )
    elif scenario_type == "Short Rate Up":
        shocked_curve["Rate"] = baseline_curve["Rate"].apply(
            lambda r, months: r + shock_magnitude_short if months <= short_term_threshold_threshold_months else r,
            months=baseline_curve["Months_to_Maturity"]
        )
    elif scenario_type == "Short Rate Down":
        shocked_curve["Rate"] = baseline_curve["Rate"].apply(
            lambda r, months: r + shock_magnitude_short if months <= short_term_threshold_months else r,
            months=baseline_curve["Months_to_Maturity"]
        )
    else:
        # No shock or invalid scenario
        pass

    return shocked_curve


@st.cache_data
def reprice_floating_instrument_cashflows_under_shock(instrument_cashflow_df, instrument_data, shocked_date_curve):
    # This function assumes instrument_data refers to a single instrument
    # and instrument_cashflow_df contains its baseline cashflows.
    if instrument_cashflow_df.empty: return instrument_cashflow_df

    repriced_cashflows = instrument_cashflow_df.copy()
    rate_type = instrument_data["Rate_Type"]
    instrument_id = instrument_data["Instrument_ID"]
    amount = instrument_data["Amount"]
    payment_frequency = instrument_data["Payment_Frequency"]

    if payment_frequency == "Monthly":
        freq_months = 1
    elif payment_frequency == "Quarterly":
        freq_months = 3
    elif payment_frequency == "Semi-Annually":
        freq_months = 6
    elif payment_frequency == "Annually":
        freq_months = 12
    else:
        freq_months = 12

    if rate_type == "Floating" or (rate_type == "Hybrid" and instrument_data["Instrument_Type"] == "Swap"):
        for idx, row in repriced_cashflows.iterrows():
            if row["Type"] == "Interest":
                cf_date = row["Cashflow_Date"]
                valuation_date_for_reprice = shocked_date_curve["Valuation_Date"].iloc[0] # Assuming valuation date is constant

                # Calculate months from valuation date to cashflow date to find relevant rate on shocked curve
                months_to_cf = round((cf_date - valuation_date_for_reprice).days / 30.44)
                months_to_cf = max(0, months_to_cf)

                # Find the rate from the shocked curve by interpolating or finding closest tenor
                # Ensure we have the full tenor range for lookup from shocked_date_curve
                if not shocked_date_curve.empty:
                    # Find closest tenor rate, or interpolate
                    if months_to_cf <= shocked_date_curve["Months_to_Maturity"].max() and months_to_cf >= shocked_date_curve["Months_to_Maturity"].min():
                        # Using interpolation for robustness
                        interp_func = interp1d(
                            shocked_date_curve["Months_to_Maturity"],
                            shocked_date_curve["Rate"],
                            kind="linear",
                            fill_value="extrapolate"
                        )
                        current_shocked_rate = interp_func(months_to_cf).item()
                    else:
                        # Extrapolate or use nearest if outside known range
                        if months_to_cf < shocked_date_curve["Months_to_Maturity"].min():
                            current_shocked_rate = shocked_date_curve["Rate"].iloc[0]
                        else:
                            current_shocked_rate = shocked_date_curve["Rate"].iloc[-1]
                else:
                    current_shocked_rate = 0.0 # Fallback if curve is empty

                # Adjust for swap floating spread if applicable
                floating_spread = instrument_data["Specific_Features"].get("floating_spread", 0.0)
                adjusted_rate = current_shocked_rate + floating_spread

                # Recalculate interest payment based on the new rate
                new_interest_payment = amount * adjusted_rate * (freq_months / 12)
                repriced_cashflows.loc[idx, "Cashflow_Amount"] = new_interest_payment if instrument_data["Is_Asset"] else -new_interest_payment

    return repriced_cashflows

@st.cache_data
def adjust_behavioral_assumptions_for_shock(cashflow_df, scenario_type, baseline_prepayment_rate, shock_adjustment_factor):
    modified_cashflow_df = cashflow_df.copy()

    # Example: Adjust prepayment rate under certain shock scenarios
    # For simplification, let's assume prepayment increases with rate cuts (down scenarios) and decreases with rate hikes (up scenarios)
    # This is a very simple rule, real models are complex (e.g., PSA models respond to "refinancing incentive")

    # Get the original instrument ID and type to check behavioral flag
    if modified_cashflow_df.empty: return modified_cashflow_df
    instrument_id = modified_cashflow_df["Instrument_ID"].iloc[0] # Assuming all cashflows belong to one instrument
    # For this function to be fully general, it would need the instrument type passed in
    # For now, let's assume it's called specifically for mortgage instruments if needed.

    # If it's a mortgage, and a principal cashflow exists:
    if "Prepayment" in modified_cashflow_df["Type"].values or (
        "Principal" in modified_cashflow_df["Type"].values and 
        "Mortgage" in instrument_id # A hacky way to check instrument type without passing it
    ):
        # Find the prepayment row if it exists, or the main principal row
        principal_or_prepayment_idx = modified_cashflow_df[modified_cashflow_df["Type"].isin(["Principal", "Prepayment"])].index
        if not principal_or_prepayment_idx.empty:
            original_cashflow_amount = modified_cashflow_df.loc[principal_or_prepayment_idx[0], "Cashflow_Amount"] # Use first found
            
            adjusted_prepayment_rate = baseline_prepayment_rate
            if "Down" in scenario_type: # Rates going down, higher incentive to prepay
                adjusted_prepayment_rate = min(baseline_prepayment_rate * (1 + shock_adjustment_factor), 1.0) # Cap at 100%
            elif "Up" in scenario_type: # Rates going up, lower incentive to prepay
                adjusted_prepayment_rate = max(baseline_prepayment_rate * (1 - shock_adjustment_factor), 0.0) # Floor at 0%
            
            # Re-apply the prepayment logic with the adjusted rate
            # This is simplified; ideally, the entire cash flow generation for mortgages would be rerun
            # with the new prepayment rate.
            # For a quick demonstration: if there was an explicit prepayment line, adjust its value.
            # If not, assume the "Prepayment" type means it was already calculated from baseline_prepayment_rate.
            
            # This requires knowing the original contractual principal and how prepayment was applied.
            # Given the previous `apply_behavioral_assumptions` for prepayment, it modifies the original principal.
            # A proper implementation would recalculate cash flows based on new prepayment curves.
            
            # For a quick fix, if "Prepayment" exists, adjust its magnitude based on the new rate relative to old.
            prepayment_rows = modified_cashflow_df[modified_cashflow_df["Type"] == "Prepayment"]
            if not prepayment_rows.empty:
                for idx in prepayment_rows.index:
                    original_prepayment_amount = abs(prepayment_rows.loc[idx, "Cashflow_Amount"])
                    # This logic is problematic because `original_prepayment_amount` already reflects baseline_prepayment_rate
                    # To truly adjust, we need the initial principal and re-apply prepayment logic.
                    # For this demo, let's assume a proportional adjustment to the existing prepayment entry if it exists
                    # This is not financially rigorous but serves the purpose of showing change.
                    
                    # If `apply_behavioral_assumptions` creates a `Prepayment` row, we can re-scale it
                    # based on the ratio of new_rate / old_rate.
                    # This is extremely simplified.
                    if baseline_prepayment_rate > 0:
                        scaling_factor = adjusted_prepayment_rate / baseline_prepayment_rate
                        modified_cashflow_df.loc[idx, "Cashflow_Amount"] *= scaling_factor
                    else:
                        # If baseline was 0, and now it's >0, we need to create it. This is complex.
                        pass # Avoid complex re-creation here


    # NMD behavioral maturity: this typically doesn't change with shock scenarios directly
    # NMD Beta: The beta affects how the NMD rate reprices, which then affects cashflows.
    # This is handled by adjusting the discount curve for NMD-like liabilities or adjusting their rates.
    # For this framework, NMD beta could be incorporated into effective discount rate for NMD PV calculation.

    return modified_cashflow_df


@st.cache_data
def recalculate_cashflows_and_pv_for_scenario(
    portfolio_df,
    shocked_curve_date_based,
    valuation_date,
    scenario_type,
    baseline_prepayment_rate, # Needed for behavioral adjustment
    behavioral_shock_adjustment_factor, # Needed for behavioral adjustment
    nmd_beta,
    nmd_behavioral_maturity_years
):
    all_shocked_cashflows = []
    for _, instrument_data in portfolio_df.iterrows():
        # 1. Generate baseline cashflows for the instrument first
        instrument_baseline_cfs = calculate_cashflows_for_instrument(
            instrument_data, shocked_curve_date_based # Use shocked curve for current rates if floating
        )

        # 2. Apply behavioral assumptions
        behavioral_flag = None
        if instrument_data["Instrument_Type"] == "Mortgage" and instrument_data["Specific_Features"].get("prepayment_option"):
            behavioral_flag = "Mortgage"
        elif instrument_data["Instrument_Type"] == "Deposit" and instrument_data["Specific_Features"].get("nmd_flag"):
            behavioral_flag = "NMD"

        if behavioral_flag:
            instrument_cfs_after_behavioral = apply_behavioral_assumptions(
                instrument_baseline_cfs,
                behavioral_flag,
                baseline_prepayment_rate, # Base rate
                nmd_beta,
                nmd_behavioral_maturity_years
            )
        else:
            instrument_cfs_after_behavioral = instrument_baseline_cfs.copy()

        # 3. Reprice floating cashflows under shock if applicable
        if instrument_data["Rate_Type"] == "Floating" or (instrument_data["Rate_Type"] == "Hybrid" and instrument_data["Instrument_Type"] == "Swap"):
            instrument_cfs_reprice_shocked = reprice_floating_instrument_cashflows_under_shock(
                instrument_cfs_after_behavioral, instrument_data, shocked_curve_date_based
            )
        else:
            instrument_cfs_reprice_shocked = instrument_cfs_after_behavioral.copy()

        # 4. Adjust behavioral assumptions specifically for shock scenario if needed
        # This step is for the *change* due to shock (e.g., higher prepayment in down scenario)
        if behavioral_flag == "Mortgage": # Only apply shock adjustment to mortgages for prepayment
             instrument_cfs_final = adjust_behavioral_assumptions_for_shock(
                instrument_cfs_reprice_shocked,
                scenario_type,
                baseline_prepayment_rate,
                behavioral_shock_adjustment_factor
            )
        else:
            instrument_cfs_final = instrument_cfs_reprice_shocked.copy()

        all_shocked_cashflows.append(instrument_cfs_final)

    # Concatenate all instrument cashflows
    if not all_shocked_cashflows: return 0.0, 0.0, 0.0 # Return 0s if no cashflows
    total_shocked_cashflows_df = pd.concat(all_shocked_cashflows, ignore_index=True)

    # Separate assets and liabilities for PV calculation
    pv_assets_shocked = 0.0
    pv_liabilities_shocked = 0.0

    assets_cfs = total_shocked_cashflows_df[total_shocked_cashflows_df["Cashflow_Amount"] > 0]
    liabilities_cfs = total_shocked_cashflows_df[total_shocked_cashflows_df["Cashflow_Amount"] <= 0]

    pv_assets_shocked = calculate_present_value_for_cashflows(assets_cfs, shocked_curve_date_based, valuation_date)
    pv_liabilities_shocked = calculate_present_value_for_cashflows(liabilities_cfs, shocked_curve_date_based, valuation_date)

    eve_shocked = calculate_eve(pv_assets_shocked, pv_liabilities_shocked)

    return eve_shocked, pv_assets_shocked, pv_liabilities_shocked


@st.cache_data
def calculate_delta_eve(baseline_eve, shocked_eve):
    return shocked_eve - baseline_eve

@st.cache_data
def report_delta_eve_as_percentage_of_tier1(delta_eve_results, tier1_capital):
    report = {}
    for scenario, delta_eve_val in delta_eve_results.items():
        if tier1_capital != 0:
            percentage = (delta_eve_val / tier1_capital) * 100
        else:
            percentage = 0.0 # Handle division by zero
        report[scenario] = percentage
    return report


"""