library(tidyverse)

# Load data
macc <- read_csv("output/data/macc_ed_early.csv")

# Map t index to year
year_map <- c("1" = 2015, "2" = 2020, "3" = 2025)

# Filter to linear coefficient only
macc_a <- macc %>%
  filter(Dim2 == "a") %>%
  mutate(year = year_map[t]) %>%
  filter(Val > 0)  # drop missing (zero) values

# Loop over years
for (yr in unique(macc_a$year)) {
  
  plot_data <- macc_a %>%
    filter(year == yr) %>%
    arrange(desc(Val))
  
  p <- ggplot(plot_data, aes(x = reorder(n, -Val), y = Val)) +
    geom_bar(stat = "identity", fill = "steelblue") +
    labs(
      title    = paste("Marginal Abatement Cost Curve — Linear Coefficient (a)"),
      subtitle = paste("Year:", yr),
      x        = "Region",
      y        = "$/tCO2",
      caption  = "Source: Enerdata/POLES via RICE50+. Shows coefficient 'a' of MAC(μ) = a·μ + d·μ⁴.\nZero values (missing coverage) excluded."
    ) +
    theme_minimal() +
    theme(
      axis.text.x      = element_text(angle = 45, hjust = 1, size = 8),
      plot.title       = element_text(face = "bold"),
      plot.subtitle    = element_text(color = "grey40"),
      plot.caption     = element_text(color = "grey50", size = 7)
    )
  
  ggsave(
    filename = paste0("output/charts/macc_a_", yr, ".png"),
    plot     = p,
    width    = 12,
    height   = 6,
    dpi      = 150
  )
  
  message("Saved macc_a_", yr, ".png")
}