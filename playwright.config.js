const {defineConfig}=require('@playwright/test');
module.exports=defineConfig({
  testDir:'./browser-tests',workers:1,retries:0,
  use:{baseURL:'http://127.0.0.1:8765',browserName:'chromium'},
  webServer:{command:'python -m gunicorn -c gunicorn.conf.py --bind 127.0.0.1:8765 "clinical_trial.wsgi:create_app()"',
    url:'http://127.0.0.1:8765/health',reuseExistingServer:false,
    env:{REVIEWER_TOKENS_JSON:JSON.stringify({'browser-test-only-token-not-for-deployment':'browser-reviewer'}),
      REVIEW_DATABASE:'local-data/browser-tests.db',ENABLE_AZURE_MODEL:'false'}}
});
