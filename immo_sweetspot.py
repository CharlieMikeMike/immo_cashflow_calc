import streamlit as st
import pandas as pd

def calculate_results(data):
    results = []
    total_cashflow = 0
    total_tax_savings = 0

    for i, row in data.iterrows():
        miet_einnahmen = row['Mieteinnahmen p.a.']
        zinssatz = row['Zinssatz %'] / 100
        tilgungsrate = row['Tilgungsrate %'] / 100
        darlehenssumme = row['Kaufpreis'] * (row['Fremdkapitalquote %'] / 100)
        zinskosten = darlehenssumme * zinssatz
        tilgung = darlehenssumme * tilgungsrate
        afa_rate = row['Gebäudeanteil %'] / 100 * row['Kaufpreis'] * 0.02
        betriebskosten = row['Betriebskosten p.a.']

        steuerlicher_gewinn = miet_einnahmen - (zinskosten + afa_rate + betriebskosten)
        steuerlast = max(0, steuerlicher_gewinn) * (row['persönlicher Steuersatz %'] / 100)
        steuerrückerstattung = abs(min(0, steuerlicher_gewinn)) * (row['persönlicher Steuersatz %'] / 100)

        # Cashflow inkl. Steuerrückerstattung
        cashflow = miet_einnahmen - (zinskosten + tilgung + betriebskosten + steuerlast) + steuerrückerstattung

        total_cashflow += cashflow
        total_tax_savings += steuerrückerstattung

        results.append({
            'Wohnung': row['Wohnung'],
            'Steuerlicher Gewinn (€)': steuerlicher_gewinn,
            'Steuerrückerstattung (€)': steuerrückerstattung,
            'Jährlicher Cashflow inkl. Steuerrückerstattung (€)': cashflow
        })

    return pd.DataFrame(results), total_cashflow, total_tax_savings

def main():
    st.title("📊 Immobilien Finanzierungs- & Steueroptimierungsmodell")
    st.write("Optimierung für mehrere Wohnungen mit live Schiebereglern")

    wohnungen = st.number_input("Anzahl Wohnungen", min_value=1, max_value=20, value=3)

    data = pd.DataFrame({
        'Wohnung': [f'Wohnung {i+1}' for i in range(wohnungen)],
        'Kaufpreis': [300000] * wohnungen,
        'Wohnfläche (qm)': [75] * wohnungen,
        'Gebäudeanteil %': [80] * wohnungen,
        'Mieteinnahmen p.a.': [14400] * wohnungen,
        'Zinssatz %': [3.0] * wohnungen,
        'Fremdkapitalquote %': [100] * wohnungen,
        'Tilgungsrate %': [2.0] * wohnungen,
        'Betriebskosten p.a.': [1500] * wohnungen,
        'Betriebskosten €/qm': [5.0] * wohnungen,
        'persönlicher Steuersatz %': [42] * wohnungen
    })

    for i in range(wohnungen):
        st.subheader(f"🏠 {data.loc[i, 'Wohnung']}")
        data.loc[i, 'Kaufpreis'] = st.slider(f"Kaufpreis {i+1} (€)", 50000, 1000000, int(data.loc[i, 'Kaufpreis']), step=10000)
        data.loc[i, 'Wohnfläche (qm)'] = st.slider(f"Wohnfläche {i+1} (qm)", 20, 300, int(data.loc[i, 'Wohnfläche (qm)']), step=5)
        data.loc[i, 'Gebäudeanteil %'] = st.slider(f"Gebäudeanteil {i+1} (%)", 50, 100, int(data.loc[i, 'Gebäudeanteil %']), step=1)
        data.loc[i, 'Mieteinnahmen p.a.'] = st.slider(f"Mieteinnahmen {i+1} p.a. (€)", 5000, 40000, int(data.loc[i, 'Mieteinnahmen p.a.']), step=500)
        data.loc[i, 'Zinssatz %'] = st.slider(f"Zinssatz {i+1} (%)", 1.0, 10.0, float(data.loc[i, 'Zinssatz %']), step=0.1)
        data.loc[i, 'Fremdkapitalquote %'] = st.slider(f"Fremdkapitalquote {i+1} (%)", 50, 110, int(data.loc[i, 'Fremdkapitalquote %']), step=1)
        data.loc[i, 'Tilgungsrate %'] = st.slider(f"Tilgungsrate {i+1} (%)", 0.0, 10.0, float(data.loc[i, 'Tilgungsrate %']), step=0.1)

        # Betriebskosten: entweder Summe direkt angeben oder aus €/qm berechnen
        betriebskosten_qm = st.slider(f"Betriebskosten {i+1} €/qm (monatlich)", 1.0, 8.0, float(data.loc[i, 'Betriebskosten €/qm']), step=0.1)
        berechnete_summe = round(betriebskosten_qm * data.loc[i, 'Wohnfläche (qm)'] * 12, 2)

        min_summe = int(1.0 * data.loc[i, 'Wohnfläche (qm)'] * 12)
        max_summe = int(8.0 * data.loc[i, 'Wohnfläche (qm)'] * 12)

        betriebskosten_summe = st.slider(f"Betriebskosten {i+1} p.a. (€)", min_summe, max_summe, int(berechnete_summe), step=100)

        # Logik: wenn der Nutzer die Summe verändert, passe €/qm an; sonst Summe aus €/qm berechnen
        if betriebskosten_summe != int(berechnete_summe):
            data.loc[i, 'Betriebskosten p.a.'] = betriebskosten_summe
            data.loc[i, 'Betriebskosten €/qm'] = round(betriebskosten_summe / (data.loc[i, 'Wohnfläche (qm)'] * 12), 2)
        else:
            data.loc[i, 'Betriebskosten €/qm'] = betriebskosten_qm
            data.loc[i, 'Betriebskosten p.a.'] = berechnete_summe

    st.subheader("💼 Persönliche Parameter")
    data['persönlicher Steuersatz %'] = st.slider("Persönlicher Steuersatz (%)", 0, 50, int(data['persönlicher Steuersatz %'][0]), step=1)

    results_df, total_cashflow, total_tax_savings = calculate_results(data)

    st.subheader("📋 Ergebnis je Wohnung")
    st.dataframe(results_df)

    st.subheader("🔑 Gesamtergebnisse")
    st.metric("Gesamter jährlicher Cashflow inkl. Steuerrückerstattung (€)", f"{total_cashflow:,.2f}")
    st.metric("Gesamte Steuerrückerstattung (€)", f"{total_tax_savings:,.2f}")

if __name__ == "__main__":
    main()
