import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import geopandas as gpd


st.set_page_config(layout="wide", page_title="Coffee Analysis")
tab1, tab2 = st.tabs(["Historical Data", "Sources"])


with tab1:
    st.title("Coffee Dashboard", text_alignment="center")

# Fetch the Production data
coffee_production_df = pd.read_csv('coffee-bean-production(2000-23).csv')
individual_countries = coffee_production_df[coffee_production_df["Code"].notna() & ~coffee_production_df["Code"].str.startswith("OWID_", na=False)].reset_index(drop=True)
regions = coffee_production_df[coffee_production_df["Code"].isna() | coffee_production_df["Code"].str.startswith("OWID_", na=False)].reset_index(drop=True)

# World Totals Grouped by Year
world_totals = regions[regions["Code"] == "OWID_WRL"]
world_totals_by_year = world_totals.groupby("Year")["Total_GreenBeans_Tonnes"].sum().reset_index()

# Total amount Produced 23 year period
total_tonnes_produced_23_years = world_totals_by_year["Total_GreenBeans_Tonnes"].sum()

# Added Unit Million Tonnes
individual_countries["Total_million_tonnes"] = individual_countries["Total_GreenBeans_Tonnes"] / 1_000_000

total_averages_by_countries_23_years = (
    individual_countries.groupby(["Code", "Entity"])
    ["Total_GreenBeans_Tonnes"]
    .sum()
    .reset_index()
)

# Add the percentage column (% of all global output for 2000-2023)
total_averages_by_countries_23_years["Share %"] = (
    total_averages_by_countries_23_years["Total_GreenBeans_Tonnes"] / 
    total_tonnes_produced_23_years * 100
).round(3)

# SORT
total_averages_by_countries_23_years = total_averages_by_countries_23_years.sort_values(
    "Total_GreenBeans_Tonnes", 
    ascending=False
).reset_index()


# Top 10 Scatter Geo Map: 
top_10 = total_averages_by_countries_23_years.nlargest(10, 'Share %')
top_10["Total_million_tonnes"] = top_10["Total_GreenBeans_Tonnes"] / 1_000_000

top_10_scatter_map = px.scatter_geo(
        top_10,
        locations="Code",
        locationmode="ISO-3",
        size="Total_million_tonnes", 
        hover_data= {
            "Entity": True, 
            "Share %": True,
            "Total_million_tonnes": True,
            "Code": False       
        },
        projection="equirectangular",
        opacity=.7,
        height=400
    )

top_10_scatter_map.update_traces(
    marker=dict(
        size= top_10["Total_million_tonnes"]* 4,
        color="#556B2F",  # circle color
    ),
    hovertemplate=(
    "<b>%{customdata[0]}</b><br>"
    "%{customdata[1]}%<br>"
    "%{customdata[2]:,.1f} million tonnes<extra></extra>"
    )
)

top_10_scatter_map.update_geos(
    showframe=False,
    showcoastlines=True,
    coastlinecolor="#333333",
    coastlinewidth=.5,
    showland=True,
    landcolor="#f7f7f7",
    showcountries=True,
    countrycolor="#333333",
    countrywidth=1,
    showocean=True,
    oceancolor="#EDF2F4",
    showlakes=True,
    lakecolor="#EDF2F4",
)

top_10_scatter_map.update_layout(
    font= {'family': 'Sans Serif'},
    margin=dict(t=40, b=0, l=0, r=0)  # Reduce top margin
)

# Coffee Belt Northern boundary (Tropic of Cancer ~23.5°N)
top_10_scatter_map.add_trace(go.Scattergeo(
    lon=list(range(-180, 181, 5)),
    lat=[23.5] * len(list(range(-180, 181, 5))),
    mode='lines',
    line=dict(color='#8B4513', width=2, dash='dash'),
    opacity=0.4,  # Add this for soft lines
    name='Coffee Belt (North)',
    showlegend=True,
    hoverinfo='skip'
))

# Coffee Belt Southern boundary (Tropic of Capricorn ~23.5°S)
top_10_scatter_map.add_trace(go.Scattergeo(
    lon=list(range(-180, 181, 5)),
    lat=[-23.5] * len(list(range(-180, 181, 5))),
    mode='lines',
    line=dict(color='#8B4513', width=2, dash='dash'),
    opacity=0.4,  # Add this for soft lines
    name='Coffee Belt (South)',
    showlegend=True,
    hoverinfo='skip'
))


color_palette = [
    # Brown, Oranges and Greens (earthy, muted)
    "#2B1E18",  # Dark Espresso 
    "#C07A4A",  # Dusty Orange
    "#7B8C69",  # Soft Olive 
    "#7A5F48",  # Medium Brown
    "#B47C5A",  # Muted Copper 
    "#9DBF9E",  # Sage Green
    "#BCAAA4",  # Light Coffee 
    "#D8B49B",  # Soft Peach 
    "#869977",  # Dusty Fern 
    "#A68A7C",  # Muted Mocha 
    "#E0A678",  # Warm Tan 
    "#A3B18A",  # Soft Mint 
    "#C4A484",  # Soft Clay 
    "#9C6D4E",  # Rusty Orange
    "#7B8C69",  # Olive Green 
]

# Top 15 Pie Chart
top_15 = total_averages_by_countries_23_years.nlargest(20, 'Share %')
others = total_averages_by_countries_23_years.drop(top_15.index)

other_row = pd.DataFrame({
    'Entity': ['All Other'],
    'Share %': [others['Share %'].sum()],

})
pie_data = pd.concat([top_15, other_row], ignore_index=True)

# Chart
top_15_pie_chart = px.pie(pie_data, values='Share %', names='Entity',color_discrete_sequence=color_palette)
top_15_pie_chart.update_traces(
    hovertemplate="<b>%{label}</b><br>%{value}%<extra></extra>"
)

with tab1:
    st.header("Production")
    st.markdown("Coffee production is highly concentrated: from 2000–2023, **Brazil**, **Vietnam**, and **Colombia** produced over 50% of global output. The top 5 countries account for ~65%, the top 10 for ~80%, and the top 20 for ~91%.")


# 1. Total per year
total_production_by_year = (
    individual_countries.groupby("Year")["Total_GreenBeans_Tonnes"]
    .sum()
    .reset_index()
    .rename(columns={"Total_GreenBeans_Tonnes": "Total_Year_Tonnes"})
)

# 2. Year + Country totals
yearly_country_totals = (
    individual_countries.groupby(["Year", "Entity"])["Total_GreenBeans_Tonnes"]
    .sum()
    .reset_index()
)

# 3. Merge totals
yearly_country_totals = yearly_country_totals.merge(total_production_by_year, on="Year")

# 4. Country order
country_totals = (
    individual_countries.groupby("Entity")["Total_GreenBeans_Tonnes"]
    .sum()
    .sort_values(ascending=False)
)
ordered_countries = country_totals.index.tolist()

# 5. Apply categorical ordering
yearly_country_totals["Entity"] = yearly_country_totals["Entity"].astype(
    pd.CategoricalDtype(categories=ordered_countries, ordered=True)
)

# 6. Sort 
yearly_country_totals = yearly_country_totals.sort_values(["Year", "Entity"])

# 7. Make chart
bar_fig = px.bar(
    yearly_country_totals,
    x="Year",
    y="Total_GreenBeans_Tonnes",
    color="Entity",
    labels={"Total_GreenBeans_Tonnes": "Production (Tonnes)", "Entity": "Country"},
    color_discrete_sequence=color_palette,
    height=500
)

bar_fig.update_layout(
    barmode="stack",
    title="Total Coffee Production by Country (Tonnes) 2000-2023",
    title_x=0.35,
    font={"family": "Serif"}
)

bar_fig.update_traces(
    hovertemplate=(
        "%{x}<br>"
        "%{fullData.name}: %{y:,.0f} tonnes<br>"
        "<span style='color:#555;'>Total that year: %{customdata[0]:,.0f} tonnes</span>"
        "<extra></extra>"
    )
)

# 8. Attach correct customdata TRACE-BY-TRACE
for entity, trace in zip(ordered_countries, bar_fig.data):
    mask = yearly_country_totals["Entity"] == entity
    trace.customdata = yearly_country_totals.loc[mask, ["Total_Year_Tonnes"]].values

with tab1:
    st.write(bar_fig)
    st.markdown("<h5 style='text-align: center;'>Top Coffee Producers, Cumulative 2000–2023</h5>", unsafe_allow_html=True)
    st.markdown("The Coffee Belt is the equatorial band where coffee grows best. All top 10 producers fall within this region. ")


with tab1:
    col1, col2 = st.columns([3, 2])

    with col1:        
        st.plotly_chart(top_10_scatter_map)
    with col2:
        st.plotly_chart(top_15_pie_chart)
    
    st.header("Consumption")

# Heat Map // Cholreomap with top consumers
# doing per capita will be fun, like what % of the people in the country drink/ instead of total country
consumption_data = pd.read_csv("Coffee Consumption(Sheet1).csv")

consumption_country_totals = (
    consumption_data.groupby("Country")["Thousand Units (Bags of 60 kg)"]
    .sum()
    .reset_index()
    .rename(columns={"Thousand Units (Bags of 60 kg)": "Total Coffee (Tonnes)"})
)

consumption_country_totals["Total Coffee (Tonnes)"] = consumption_country_totals["Total Coffee (Tonnes)"] * 60
consumption_country_totals = consumption_country_totals.sort_values(by="Total Coffee (Tonnes)", ascending=False)

# Top consumption Total
choropleth_consumption_map = px.choropleth(
    consumption_country_totals, 
    color='Total Coffee (Tonnes)', 
    color_continuous_scale=[(0, '#D2B48C'), (1, '#3E2723')],
    locations='Country', 
    locationmode='country names'
    )

# Top consumption per capita
choropleth_consumption_map2 = px.choropleth(
    consumption_country_totals.head(1), 
    color='Total Coffee (Tonnes)', 
    color_continuous_scale=[(0, '#D2B48C'), (1, '#3E2723')],
    locations='Country', 
    locationmode='country names',
    )

choropleth_consumption_map.update_geos(
    showframe=False,
    showcoastlines=True,
    coastlinecolor="#333333",
    coastlinewidth=.5,
    showland=True,
    landcolor="#f7f7f7",
    showcountries=True,
    countrycolor="#333333",
    countrywidth=1,
    showocean=True,
    oceancolor="#EDF2F4",
    showlakes=True,
    lakecolor="#EDF2F4",
)

# Total Consumption map
choropleth_consumption_map.update_traces(
    hovertemplate="<b>%{location}</b><br>%{z:,.0f} tonnes<extra></extra>"
)


with tab1:
    col3, col4 = st.columns([1,3])
    with col3:
        st.markdown("The **United States** leads global coffee consumption at **37.8 million tonnes**, followed by **Brazil** (27.9M) and **Japan** (12.2M). Notable consumers also include **Russia**, **Indonesia**, and **Ethiopia** — the latter two being major producers that also consume heavily domestically. **Colombia**, **Mexico**, **Philippines**, and **Venezuela** round out the top 10.")
    with col4:
        st.plotly_chart(choropleth_consumption_map, use_container_width=True)


# Top consumption per capita
consumption_per_capita = pd.read_csv("consumption2.csv")

choropleth_consumption_map2 = px.choropleth(
    consumption_per_capita,
    locations="Country",
    locationmode="country names",
    color="Consumption(kg/person/year)",
    color_continuous_scale=[(0, '#D2B48C'), (1, '#3E2723')],
    labels={"Consumption(kg/person/year)": "kg/person/year"},
)

choropleth_consumption_map2.update_geos(
    showframe=False,
    showcoastlines=True,
    coastlinecolor="#333333",
    coastlinewidth=.5,
    showland=True,
    landcolor="#f7f7f7",
    showcountries=True,
    countrycolor="#333333",
    countrywidth=1,
    showocean=True,
    oceancolor="#EDF2F4",
    showlakes=True,
    lakecolor="#EDF2F4",
    center=dict(lat=55, lon=-40),
    projection_scale=2.5,
)

choropleth_consumption_map2.update_layout(
    margin=dict(t=40, b=0, l=0, r=0),
    font={"family": "Serif"}
)

# Per Capita map
choropleth_consumption_map2.update_traces(
    hovertemplate="<b>%{location}</b><br>%{z:.1f} kg/person/year<extra></extra>"
)

with tab1:
    col5, col6 = st.columns([3, 1])
    with col5:
        st.plotly_chart(choropleth_consumption_map2, use_container_width=True)
    with col6:
        st.markdown("Nordic countries dominate per-capita coffee consumption. **Finland** leads the world at 11.9 kg/person/year, followed by **Norway** (9.8 kg) and **Iceland** (9 kg). The top 10 is rounded out by **Denmark**, **Netherlands**, **Sweden**, **Switzerland**, **Belgium**, **Canada**, and **Austria** — all consuming over 6 kg per person annually.")
        


# Top Importers and Exports: What coffee ends up where (Brazil coffee ends up in Germany, )

import_data = pd.read_csv("coffee(unroasted green beans) import export(import).csv")
grouped_import_data = import_data.groupby("Country")["Value (t)"].sum().sort_values(ascending=False)
top_importers = grouped_import_data.head(14).reset_index()



export_data = pd.read_csv("coffee(unroasted green beans) import export(export).csv")
grouped_export_data = export_data.groupby("Country")["Value (t)"].sum().sort_values(ascending=False)
top_exporters = grouped_export_data.head(13).reset_index()



choropleth_importers_map = px.choropleth(
    top_importers,
    color="Value (t)",
    color_continuous_scale=["#AE7E40", "#8B4513", "#3E2723"],
    locations="Country",
    locationmode="country names"
)

choropleth_exporters = px.choropleth(
    top_exporters,
    locations="Country",
    locationmode="country names",
    color="Value (t)",
    color_continuous_scale=["#96D59B", "#4CAF50", "#1B5E20"],
    labels={"Value (t)": "Export Volume (tonnes)"}
)

# Update the exporter trace to use a different coloraxis
choropleth_exporters.update_traces(
    hovertemplate="<b>%{location}</b><br>%{z:,.0f} tonnes<extra></extra>",
    coloraxis="coloraxis2"
)


# Add exporter traces to the importer map
for trace in choropleth_exporters.data:
    choropleth_importers_map.add_trace(trace)

# Configure both color axes
choropleth_importers_map.update_layout(
    title="Global Coffee Trade: Importers & Exporters 2015-2023",
    geo=dict(showframe=False, showcoastlines=True),
    height=700,
    coloraxis=dict(colorscale=["#AE7E40", "#8B4513", "#3E2723"], colorbar=dict(title="Imports (t)",  x=1)),
    coloraxis2=dict(colorscale=["#96D59B", "#4CAF50", "#1B5E20"], colorbar=dict(title="Exports (t)", x=1.1))
)

choropleth_importers_map.update_geos(
    showframe=False,
    showcoastlines=True,
    coastlinecolor="#333333",
    coastlinewidth=.5,
    showland=True,
    landcolor="#f7f7f7",
    showcountries=True,
    countrycolor="#333333",
    countrywidth=1,
    showocean=True,
    oceancolor="#EDF2F4",
    showlakes=True,
    lakecolor="#EDF2F4",
)
choropleth_importers_map.update_traces(
    hovertemplate="<b>%{location}</b><br>%{z:,.0f} tonnes<extra></extra>"
)

with tab1:
    st.header("Imports & Exports")
    st.markdown("Coffee trade follows a clear pattern: **Coffee Belt countries export**, while **North America and Western Europe import**. **Brazil** (18.4M tonnes) and **Vietnam** (12.4M) dominate exports, followed by **Colombia**, **Indonesia**, and **Honduras**. The **United States** (13.3M tonnes) is the world's largest importer, with **Germany** (9.9M) and **Italy** (5.4M) close behind. Notably, **Germany** and **Belgium** appear on *both* lists — not as growers, but due to their massive roasting and refining infrastructure, importing raw beans and re-exporting processed coffee across Europe.")
    st.plotly_chart(choropleth_importers_map, use_container_width=True)

with tab2:
    st.markdown(
    """
    <div style="font-size: 0.85rem; line-height: 1.8;">
      <p style="padding-left: 2em; text-indent: -2em;">
        International Coffee Organization. "Coffee Consumption Rankings." <em>NationMaster</em>,
        <a href="https://www.nationmaster.com/nmx/ranking/coffee-consumption">www.nationmaster.com/nmx/ranking/coffee-consumption</a>. Accessed 6 Apr. 2026.
      </p>
      <p style="padding-left: 2em; text-indent: -2em;">
        Our World in Data. "Coffee Production by Region." <em>Our World in Data</em>,
        <a href="https://ourworldindata.org/grapher/coffee-production-by-region">ourworldindata.org/grapher/coffee-production-by-region</a>. Accessed 6 Apr. 2026.
      </p>
      <p style="padding-left: 2em; text-indent: -2em;">
        ReportLinker. "Global Coffee Industry Dataset." <em>ReportLinker</em>,
        <a href="https://www.reportlinker.com/dataset/b544a508c4dd2c4169ae5fa68479a2bef7948cf3">www.reportlinker.com/dataset/b544a508...</a>. Accessed 6 Apr. 2026.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)