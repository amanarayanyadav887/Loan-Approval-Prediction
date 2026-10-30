LOAN APPROVAL PROJECT — NETLIFY FRONTEND + RENDER PYTHON API

WHY TWO HOSTS?
Netlify hosts the HTML/CSS/JavaScript frontend. Your existing Flask +
scikit-learn Python model runs as a separate API on Render. Netlify does not
run this existing Flask app.py as a normal long-running Python web server.

1. UPLOAD TO GITHUB
Extract this ZIP. Create a GitHub repository and upload the CONTENTS of this
folder to the repository root. Include app.py, requirements.txt, render.yaml,
netlify.toml, netlify/, and data/.

2. DEPLOY PYTHON BACKEND ON RENDER
- Sign in at https://render.com/
- Choose New > Web Service and connect the GitHub repository.
- Runtime: Python
- Build command: pip install -r requirements.txt
- Start command: gunicorn app:app
- Deploy and copy the service URL, e.g. https://your-service.onrender.com.

3. CONNECT FRONTEND TO BACKEND
Edit netlify/config.js and replace YOUR-RENDER-SERVICE with your actual
Render service hostname. Example:
window.API_BASE_URL = 'https://your-service.onrender.com';
Save and push this change to GitHub.

4. DEPLOY FRONTEND ON NETLIFY
- Sign in at https://app.netlify.com/
- Add new site > Import an existing project > connect the GitHub repository.
- Build command: leave blank.
- Publish directory: netlify
- Deploy and open the generated Netlify URL.

IMPORTANT
- Deploy backend first, set its URL in netlify/config.js, then deploy/redeploy Netlify.
- Free Render services may sleep when idle and take time to wake on a later request.
- CORS is initially open to all origins for setup; restrict it to your Netlify domain
  for production.
- This is an educational prediction demo, not a real lending decision.
