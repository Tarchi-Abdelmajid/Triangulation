import logging
import azure.functions as func
import json
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Triangulated circuit conformity calculation')
    
    try:
        body = req.get_json()
        
        triangles = body.get('triangles')
        realized_coords = body.get('realized')
        prestationId = body.get('prestationId')
        
        logging.info(f"Prestation: {prestationId}, Triangles: {len(triangles)}, GPS points: {len(realized_coords)}")
        
        if not triangles or not realized_coords:
            return func.HttpResponse(
                json.dumps({"error": "Missing triangles or realized coordinates"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Convert realized GPS points to Shapely Points
        gps_points = [Point(coord) for coord in realized_coords]
        logging.info(f"Created {len(gps_points)} GPS point objects")
        
        # Create spatial index of GPS points for fast lookup
        gps_spatial_index = STRtree(gps_points)
        
        # Check each triangle if it contains any GPS point
        filled_triangles = 0
        total_triangles = len(triangles)
        
        for triangle_feature in triangles:
            coords = triangle_feature['geometry']['coordinates'][0]
            triangle_polygon = Polygon(coords)
            
            # Query spatial index to get GPS points near this triangle
            nearby_points = gps_spatial_index.query(triangle_polygon)
            
            # Check if any GPS point is inside this triangle
            for point in nearby_points:
                if triangle_polygon.contains(point):
                    filled_triangles += 1
                    break  # Found one point inside, mark triangle as filled and move to next triangle
        
        # Calculate percentage: filled triangles / total triangles
        percentage = (filled_triangles / total_triangles) * 100 if total_triangles > 0 else 0
        
        logging.info(f"Result: {filled_triangles}/{total_triangles} triangles filled = {percentage:.2f}%")
        
        return func.HttpResponse(
            json.dumps({"percentage_inside": percentage}),
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
