from debug import plot_comparisons_with_fit
x = [0.1,0.2,0.3,0.4,0.5], [0.1,0.2,0.3,0.4,0.5], [0.1,0.24,0.3,0.4,0.5], [0.1,0.2,0.3,0.4,0.5]
y = [0.1,0.2,0.3,0.4,0.5], [0.11,0.21,0.31,0.41,0.51], [0.12,0.23,0.33,0.43,0.55], [0.1,0.2,0.3,0.4,0.5]
esperiments = {}
for i in range(len(x)):
    esperiment = (x,y)
    esperiments[i] = {
        "esperiment": esperiment,
        "lin": None
    }


    
plot_comparisons_with_fit(esperiments)