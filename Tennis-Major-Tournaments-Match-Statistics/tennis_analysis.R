library(knitr)
opts_chunk$set(fig.align="center", fig.height=4, fig.width=5)
library(ggplot2)
theme_set(theme_bw(base_size=12))
library(dplyr)
library(tidyr)
library(grid)

data = read.csv("Tennis-Major-Tournaments-Match-Statistics/data/FrenchOpen-men-2013.csv", header = TRUE)
head(data)

# Delete columns with unit variance
data[,sapply(data, function(v) var(v, na.rm=TRUE)!=0)] -> data

na.omit(data)

# Perform PCA
na.omit(data) %>% select(-Player1, -Player2) %>% scale() %>% prcomp() -> pca

head(pca$x)

rotation_data <- data.frame(pca$rotation, variable=row.names(pca$rotation))
arrow_style <- arrow(length = unit(0.05, "inches"),
                     type = "closed")

ggplot(rotation_data) + 
  geom_segment(aes(xend=PC1, yend=PC2), x=0, y=0, arrow=arrow_style) + 
  geom_text(aes(x=PC1, y=PC2, label=variable), hjust=0, size=3, color='red') + 
  xlim(-.5,.5) + 
  ylim(-.5,.25) +
  coord_fixed()


# Percentage of variance explained

percent <- 100*pca$sdev^2/sum(pca$sdev^2)
percent

perc_data <- data.frame(percent=percent, PC=1:length(percent))
ggplot(perc_data, aes(x=PC, y=percent, fill=percent)) + 
  geom_bar(stat="identity") + 
  geom_text(aes(label=round(percent, 2)), size=4, vjust=-.5) + 
  ylim(0, 80)

