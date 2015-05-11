from flask import Flask, render_template, url_for, jsonify, request
from sitemap.parser import get_sitemap


app = Flask(__name__)
MAX_FILESIZE = 10485760 # 10MB


@app.route("/")
def index():
    return render_template('index.html')

@app.route('/generate_sitemap', methods=['POST'])
def sitemap():
	url = request.form['url']
	warnings = []

	# Handle env errors while making sitemap.xml
	try:
		result = get_sitemap(url)
	except EnvironmentError:
		return jsonify(errors=['Server couldn\'t make sitemap.xml right now..'])
	else:
		if isinstance(result, list):
			return jsonify(errors=result)
		if result[1] > 50000:
			warnings.append('Warning! Your sitemap.xml consist more than 50.000 URLs')
		if result[2] > MAX_FILESIZE:
			warnings.append('Warning! Your sitemap.xml greater than 10 MB')
		else:
			return jsonify(data=url_for('static', filename=result[0]), warnings=warnings)

if __name__ == "__main__":
    app.run(debug=True)