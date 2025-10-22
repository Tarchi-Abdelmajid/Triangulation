import logging
import azure.functions as func
import json
from shapely.geometry import LineString, Point, MultiPolygon
from shapely.ops import unary_union

class CircuitAnalysis:
    def __init__(self):
        self.theoretical_circuit = None
        self.realized_circuit = None
        self.percent_inside = 0
    
    def set_theoretical_circuit(self, coords):
        logging.info(f"Setting theoretical circuit with {len(coords)} coordinates")
        self.theoretical_circuit = LineString(coords)
        logging.info(f"Theoretical circuit created successfully")
    
    def set_realized_circuit(self, coords, buffer_dist=0.0002):
        logging.info(f"Setting realized circuit with {len(coords)} coordinates, buffer={buffer_dist}")
        try:
            self.realized_circuit = LineString(coords)
            logging.info("Realized LineString created")
            
            self.dilated_realized = self.realized_circuit.buffer(buffer_dist)
            logging.info("Buffer operation completed")
        except Exception as e:
            logging.error(f"Error in set_realized_circuit: {str(e)}")
            raise
    
    def calculate_percentage_inside(self):
        logging.info("Starting percentage calculation")
        if not self.theoretical_circuit or not self.realized_circuit:
            logging.warning("Missing circuit data")
            return 0
        
        try:
            points_inside = sum(Point(point).within(self.dilated_realized) for point in self.theoretical_circuit.coords)
            total_points = len(self.theoretical_circuit.coords)
            self.percent_inside = (points_inside / total_points) * 100 if total_points > 0 else 0
            logging.info(f"Calculation complete: {points_inside}/{total_points} points inside = {self.percent_inside}%")
        except Exception as e:
            logging.error(f"Error in calculate_percentage_inside: {str(e)}")
            raise
    
    def get_percentage_inside(self):
        return self.percent_inside

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    try:
        body = req.get_json()
        logging.info("Request body parsed successfully")
        
        theoretical_coords = body.get('theoretical')
        realized_coords = body.get('realized')
        prestationId = body.get('prestationId')
        
        logging.info(f"Prestation ID: {prestationId}")
        logging.info(f"Theoretical coords count: {len(theoretical_coords) if theoretical_coords else 0}")
        logging.info(f"Realized coords count: {len(realized_coords) if realized_coords else 0}")
        
        if prestationId in [2, 10]:
            buffer_dist = 0.00027
        elif prestationId in [4, 9, 22, 23]:
            buffer_dist = 0.00027
        elif prestationId in [6, 8]:
            buffer_dist = 0.000236
        elif prestationId == 64:
            buffer_dist = 0.00005
        else:
            buffer_dist = 0.00027
        
        logging.info(f"Buffer distance: {buffer_dist}")
        
        if not theoretical_coords or not realized_coords:
            logging.warning("Missing coordinates in request")
            return func.HttpResponse(
                "Please pass the coordinates for both theoretical and realized circuits in the request body",
                status_code=400
            )
        
        circuit_analysis = CircuitAnalysis()
        
        logging.info("Setting theoretical circuit...")
        circuit_analysis.set_theoretical_circuit(theoretical_coords)
        
        logging.info("Setting realized circuit...")
        circuit_analysis.set_realized_circuit(realized_coords, buffer_dist)
        
        logging.info("Calculating percentage...")
        circuit_analysis.calculate_percentage_inside()
        
        result = circuit_analysis.get_percentage_inside()
        logging.info(f"Final result: {result}%")
        
        return func.HttpResponse(
            json.dumps({"percentage_inside": result}),
            mimetype="application/json"
        )
    
    except ValueError as e:
        logging.error(f"ValueError: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Invalid input: {str(e)}"}),
            status_code=400,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": f"Internal error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
