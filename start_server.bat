@echo off
echo Starte DSR Prototype im Netzwerk-Modus...
echo Teilnehmer koennen zugreifen unter: http://DEINE-IP:8501
echo (Die genaue IP wird in der App angezeigt)
echo.
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
pause
