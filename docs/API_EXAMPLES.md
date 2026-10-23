# API examples

Base URL: your deployed Vercel URL.

Public health checks:

```bash
curl https://YOUR-APP.vercel.app/health
curl https://YOUR-APP.vercel.app/health/ready
```

Student-data endpoints require the `X-API-Key` header. Set `SDIS_API_KEY` in the deployment environment and send the same value only from a trusted client:

```bash
curl -H 'X-API-Key: YOUR_API_KEY' \\
  https://YOUR-APP.vercel.app/students/1
```

Create a synthetic student:

```bash
curl -X POST https://YOUR-APP.vercel.app/students \\
  -H 'Content-Type: application/json' \\
  -H 'X-API-Key: YOUR_API_KEY' \\
  -d '{"display_name":"Synthetic Learner","grade_level":"Grade 6","preferred_language":"bn"}'
```

The API key is an interim shared-secret safeguard, not user accounts or role-based access control. Do not put it in frontend JavaScript or distribute it to students. This MVP is not approved for real student data until proper authentication, authorization, consent, and retention controls are implemented.
