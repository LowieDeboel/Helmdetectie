# Helmdetectie

Code om aan helmdetectie te doen via een GUI die de optie geeft om 
1) via tiny (20fps, minder accuraat) of normal (2fp, heel accuraat) te detecteren,
2) via een ingebouwde webcam of een externe usb-webcam te werken.

De code is zo geschreven dat via een shiftregister wordt bepaald of een persoon door een poortje mag gaan als hij al dan niet een veiligheidshelm draagt. Als het shiftregister een bepaalde hoeveelheid positieve waarden bevat, zal het poortje voor een bepaalde tijd opengaan (en pauzeert het shiftregister even) alvorens terug te sluiten en verder te gaan met detecteren.

# TODO
Window layout aanpassen en logo toevoegen
