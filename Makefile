load:
	python src/etl/loader.py

ratios:
	python src/analytics/ratios.py

test:
	pytest tests/

report:
	python src/reports/portfolio_report.py

dashboard:
	streamlit run src/dashboard/app.py

api:
	uvicorn src.api.main:app --port 8000

clean:
	Get-ChildItem -Recurse -Filter *.pyc | Remove-Item -Force
	Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force