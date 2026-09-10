import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_industrial_energy_data(filename="data/industrial_energy_data.csv", days=37):
    """
    Generates realistic 15-minute interval energy data for an industrial manufacturing facility.
    Days 1 to 30: Baseline operational period (High peak demand due to overlapping HVAC & Process loads).
    Days 31 to 37: Post-Intervention period (Pre-cooling HVAC, staggered process loads, lighting optimization).
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 96 intervals per day (15 min intervals)
    start_date = datetime(2026, 8, 1, 0, 0, 0)
    total_intervals = days * 24 * 4
    
    timestamps = [start_date + timedelta(minutes=15 * i) for i in range(total_intervals)]
    
    data = []
    
    np.random.seed(42)  # For reproducible realistic data
    
    for ts in timestamps:
        day_num = (ts - start_date).days + 1
        is_intervention = day_num > 30
        is_weekend = ts.weekday() >= 5
        hour = ts.hour + ts.minute / 60.0
        
        # Tariff structure:
        # Peak: 18:00 - 22:00 (6 PM - 10 PM)
        # Normal: 08:00 - 18:00 (8 AM - 6 PM)
        # Off-Peak: 22:00 - 08:00 (10 PM - 8 AM)
        if 18.0 <= hour < 22.0 and not is_weekend:
            tariff_period = "Peak"
            tariff_rate = 0.35  # $/kWh
        elif 8.0 <= hour < 18.0 and not is_weekend:
            tariff_period = "Normal"
            tariff_rate = 0.18  # $/kWh
        else:
            tariff_period = "Off-Peak"
            tariff_rate = 0.08  # $/kWh
            
        # Ambient Temperature Profile (°C)
        base_temp = 22.0 + 7.0 * np.sin(np.pi * (hour - 8) / 12.0)
        ambient_temp = base_temp + np.random.normal(0, 0.8)
        
        # Occupancy (%)
        if is_weekend:
            occupancy = float(np.clip(np.random.normal(10, 3), 5, 20))
        elif 7.0 <= hour < 19.0:
            occupancy = float(np.clip(85 + 10 * np.sin(np.pi * (hour - 7) / 12) + np.random.normal(0, 5), 10, 100))
        elif 19.0 <= hour < 22.0:
            # Shift ending - low occupancy during peak tariff hours!
            occupancy = float(np.clip(25 - 5 * (hour - 19) + np.random.normal(0, 3), 5, 40))
        else:
            occupancy = float(np.clip(np.random.normal(8, 2), 2, 15))
            
        # Equipment Schedule Expectations (1 = Scheduled ON, 0 = Scheduled OFF)
        hvac_scheduled = 1 if (6.0 <= hour < 18.5 and not is_weekend) else 0
        process_scheduled = 1 if (7.5 <= hour < 18.0 and not is_weekend) else 0
        lighting_scheduled = 1 if (6.5 <= hour < 20.0 and not is_weekend) else 0
        
        # Baseline vs Post-Intervention Load Modeling
        
        # 1. HVAC Load (kW)
        # Thermal load depends on temp & occupancy.
        if not is_intervention:
            # Baseline: HVAC runs hard during peak tariff (18:00-22:00) even when occupancy drops!
            if 18.0 <= hour < 22.0 and not is_weekend:
                hvac_kw = 160.0 + (ambient_temp - 20) * 4.5 + np.random.normal(0, 5)
            elif 6.0 <= hour < 18.0 and not is_weekend:
                hvac_kw = 140.0 + (ambient_temp - 20) * 4.0 + (occupancy / 100) * 30 + np.random.normal(0, 5)
            else:
                # Night background HVAC (some schedule leakage)
                hvac_kw = 55.0 + np.random.normal(0, 3)
        else:
            # Post-Intervention: Pre-cooling before peak (14:00-17:30) and throttled during peak (18:00-22:00)
            if 14.0 <= hour < 17.5 and not is_weekend:
                # Pre-cooling boost during Normal tariff
                hvac_kw = 175.0 + (ambient_temp - 20) * 4.0 + np.random.normal(0, 4)
            elif 18.0 <= hour < 22.0 and not is_weekend:
                # Throttled during Peak tariff (saving high demand charges)
                hvac_kw = 75.0 + (ambient_temp - 20) * 2.0 + np.random.normal(0, 3)
            elif 6.0 <= hour < 14.0 and not is_weekend:
                hvac_kw = 135.0 + (ambient_temp - 20) * 3.8 + (occupancy / 100) * 25 + np.random.normal(0, 4)
            else:
                hvac_kw = 35.0 + np.random.normal(0, 2)  # Strict after-hours setpoint
                
        # 2. Process Heavy Machinery Load (kW)
        if not is_intervention:
            # Baseline: High process load overlapping with 18:00-19:30 peak tariff
            if 8.0 <= hour < 19.5 and not is_weekend:
                process_kw = 280.0 + np.random.normal(0, 15)
            else:
                process_kw = 45.0 + np.random.normal(0, 5)  # Idle baseload
        else:
            # Post-Intervention: Staggered line maintenance / early ramp-down by 17:30
            if 8.0 <= hour < 17.5 and not is_weekend:
                process_kw = 290.0 + np.random.normal(0, 12)  # Slightly higher efficiency during normal hours
            elif 17.5 <= hour < 22.0 and not is_weekend:
                process_kw = 60.0 + np.random.normal(0, 5)   # Shifted off peak!
            else:
                process_kw = 40.0 + np.random.normal(0, 4)
                
        # 3. Facility Lighting Load (kW)
        if not is_intervention:
            # Baseline: Lights left ON 24/7 across warehouse & office
            if 6.0 <= hour < 22.0:
                lighting_kw = 70.0 + np.random.normal(0, 3)
            else:
                lighting_kw = 50.0 + np.random.normal(0, 2)
        else:
            # Post-Intervention: Smart occupancy sensors & automatic 20:00 cutoff
            if 6.5 <= hour < 19.0 and not is_weekend:
                lighting_kw = 55.0 + np.random.normal(0, 2)
            elif 19.0 <= hour < 22.0 and not is_weekend:
                lighting_kw = 25.0 + np.random.normal(0, 2)
            else:
                lighting_kw = 12.0 + np.random.normal(0, 1)  # Minimum safety lights
                
        # 4. Auxiliary / Data Center / Pumps Load (kW)
        aux_kw = 40.0 + np.random.normal(0, 3)
        
        # Ensure positive values
        hvac_kw = float(max(10.0, hvac_kw))
        process_kw = float(max(15.0, process_kw))
        lighting_kw = float(max(5.0, lighting_kw))
        aux_kw = float(max(10.0, aux_kw))
        
        # Total Power Consumption (kW)
        total_kw = float(round(hvac_kw + process_kw + lighting_kw + aux_kw, 2))
        
        # 15-minute interval energy consumption in kWh = kW * (15/60) = kW * 0.25
        energy_kwh = float(round(total_kw * 0.25, 3))
        
        # Production index (units per 15 min)
        if 8.0 <= hour < 17.5 and not is_weekend:
            production_units = int(np.random.poisson(120))
        elif 17.5 <= hour < 19.5 and not is_weekend and not is_intervention:
            production_units = int(np.random.poisson(90))
        else:
            production_units = 0
            
        data.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "total_kw": total_kw,
            "total_kwh": energy_kwh,
            "hvac_kw": round(hvac_kw, 2),
            "process_kw": round(process_kw, 2),
            "lighting_kw": round(lighting_kw, 2),
            "aux_kw": round(aux_kw, 2),
            "tariff_period": tariff_period,
            "tariff_rate": tariff_rate,
            "ambient_temp_c": round(ambient_temp, 1),
            "occupancy_pct": round(occupancy, 1),
            "production_units": production_units,
            "hvac_scheduled": hvac_scheduled,
            "process_scheduled": process_scheduled,
            "lighting_scheduled": lighting_scheduled,
            "is_intervention": 1 if is_intervention else 0
        })
        
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Dataset generated successfully at {filename} with {len(df)} records.")
    return df

if __name__ == "__main__":
    generate_industrial_energy_data()
