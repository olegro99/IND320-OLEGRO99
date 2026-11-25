import sys
from pathlib import Path

# Legg til "streamlit app"-mappen (en nivå opp fra Pages/) i søkestien
CURRENT_DIR = Path(__file__).parent
STREAMLIT_APP_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(STREAMLIT_APP_DIR))

from functions.water_functions import get_water_data

raw = get_water_data()

print("Alle kolonner i rådata:")
print(raw.columns.tolist())

vass = raw[raw["omrType"] == "VASS"]

for nr in sorted(vass["omrnr"].unique()):
    eksempel = vass[vass["omrnr"] == nr].iloc[0]
    print(f"\n--- omrnr = {nr} ---")
    for key, val in eksempel.to_dict().items():
        print(f"  {key}: {val}")

no_totalt = raw[(raw["omrType"] == "NO") & (raw["dato_Id"] == "2020-01-06")]
vass_sum = raw[(raw["omrType"] == "VASS") & (raw["dato_Id"] == "2020-01-06")]["kapasitet_TWh"].sum()

print("NO total kapasitet:", no_totalt["kapasitet_TWh"].values)
print("Sum av VASS 1+2+3 kapasitet:", vass_sum)