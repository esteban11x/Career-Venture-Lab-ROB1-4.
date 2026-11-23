# Career Venture Lab — ROB-1 Robotics Kit & Repair Studio

**Course:** Algebra 2  
**Level:** Advanced  
**Build phase:** Stage 1  
**Status:** Starter implementation generated for review. Run the tests before submitting or deploying.

This is a fictional classroom business simulator. It is not a real store and does not accept payments.

## Files

- `app.py` — Streamlit dashboard and controls.
- `engine.py` — business calculations, Algebra 2 calculations, snapshot rules.
- `requirements.txt` — Python packages.
- `render.yaml` — Render service settings.
- `sample_data/monthly_fixture.csv` — official three-month ROB-1 practice fixture.
- `tests/test_rob1_acceptance.py` — acceptance tests.

## Run on your computer

1. Install Python 3.11 or newer.
2. Open a terminal in this folder.
3. Install packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the tests:

   ```bash
   python -m pytest -v
   ```

5. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

The dashboard normally opens in your browser. The test command must pass before treating the build as verified.

## Deploy with GitHub and Render

1. Create a GitHub repository for your team.
2. Upload the files and folders in this project.
3. In Render, choose **New + → Web Service** and connect the repository.
4. Render should read `render.yaml`. If it asks manually:
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`
5. Deploy and open the service URL.

Do not put passwords, API keys, or private information in the repository.

## Saving your work

Use **Download snapshot JSON** in the dashboard regularly. Render's local files may be temporary, so do not assume a saved file on the server will survive a restart or redeploy. Keep a copy of your JSON snapshot on your own device and restore it with the upload control.

## Important scope notes

This is a Stage 1 implementation. The dashboard includes startup assumptions, monthly inputs, a deterministic business engine, selected Algebra 2 calculations, a dated ledger, snapshot download/import, and a separate fixture replay.

Stage 2 department assistants, report center, and full costed marketing studio; Stage 3 assessments and cross-course evidence; and Stage 4 optional storefront/API features are **not implemented** here. Some advanced accounting and workflow fields are represented in the data model but are not a substitute for teacher review.

The official fixture intentionally overrides capacity for test replay only. Normal simulation derives capacity from staff hours. Fixture replay is shown separately and does not replace your saved business state.

## Handbook assumptions used

The ROB-1 defaults and test results follow the Career Venture Lab Student Handbook:
- Starting owner contribution $12,000; equipment $4,000; opening inventory $3,000; opening spendable cash $5,000.
- Kit price $120; demand 40; staff time 90 hours/month; 3 hours/kit; 100 opening component sets at $30 each.
- Variable cost $65 per attempted kit; fixed monthly costs $600.
- Component inventory is paid for when purchased and expensed when consumed. Failed kits consume costs but do not generate sales.
- The Algebra 2 adapter supplies the break-even, demand, and extra-shift models.

See the class handbook, ROB package pages 78–82 and Algebra 2 adapter page 68, for the full assignment requirements.
