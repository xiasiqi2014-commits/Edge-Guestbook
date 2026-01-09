from workers import Response, WorkerEntrypoint
import json
import datetime

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        if request.method == "OPTIONS":
            return Response("OK", headers=cors_headers)

        url = request.url
        path = url.split("://")[-1].split("/", 1)[-1]  # Simple path parsing
        
        # 2. Router Logic
        if "api/guestbook" in url:
            if request.method == "GET":
                # D1 Query: Select all messages
                # self.env.guestbook_db is the binding we created
                try:
                    result = await self.env.guestbook_db.prepare(
                        "SELECT * FROM guestbook ORDER BY id DESC"
                    ).all()
                    
                    # result.results is a JsProxy (JS Array)
                    # We need to convert it to a Python list/dict before JSON serialization
                    results_py = result.results
                    if hasattr(results_py, "to_py"):
                        results_py = results_py.to_py()
                    
                    return Response(
                        json.dumps(results_py),
                        headers={**cors_headers, "Content-Type": "application/json"}
                    )
                except Exception as e:
                    return Response(f"Database Error: {str(e)}", status=500, headers=cors_headers)
            
            elif request.method == "POST":
                try:
                    body = await request.json()
                except Exception:
                    return Response("Invalid JSON", status=400, headers=cors_headers)
                
                user_message = body.get("message", "").strip()
                if not user_message:
                    return Response("Message cannot be empty", status=400, headers=cors_headers)

                # 3. Get Geo-Location (Robust Strategy)
                city = "Unknown City"
                country = "Unknown Country"
                try:
                    if hasattr(request, "cf") and request.cf:
                        city = getattr(request.cf, "city", city)
                        country = getattr(request.cf, "country", country)
                except Exception:
                    pass

                if city == "Unknown City":
                    city = request.headers.get("cf-ipcity", "Unknown City")
                if country == "Unknown Country":
                    country = request.headers.get("cf-ipcountry", "Unknown Country")
                
                if city == "Unknown City" and country == "Unknown Country":
                    city = "Localhost"

                location_str = f"{city}, {country}"
                timestamp_str = datetime.datetime.now().isoformat()

                # D1 Insert
                try:
                    await self.env.guestbook_db.prepare(
                        "INSERT INTO guestbook (text, location, timestamp) VALUES (?, ?, ?)"
                    ).bind(user_message, location_str, timestamp_str).run()
                    
                    # Fetch valid ID if needed, or just return success
                    return Response(
                        json.dumps({"status": "success"}),
                        status=201,
                        headers={**cors_headers, "Content-Type": "application/json"}
                    )
                except Exception as e:
                    return Response(f"Database Insert Error: {str(e)}", status=500, headers=cors_headers)
        
        return Response(
            "Not Found. Try POST/GET to /api/guestbook", 
            status=404, 
            headers=cors_headers
        )
