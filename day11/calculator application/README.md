# Calculator Cameo

A sleek, functional, and responsive web-based calculator built using vanilla HTML, CSS, and JavaScript.

## Features
- **Basic Arithmetic**: Supports addition, subtraction, multiplication, and division.
- **Clean UI**: A modern, dark-themed interface built using CSS Grid for perfect button alignment.
- **Responsive**: Adapts gracefully to screen sizes and maintains its layout.

## How to Run

Since this is a static web application, there are multiple ways to run it:

### 1. Direct File Access
Simply open the `index.html` file in any modern web browser. No server required!

### 2. Using Docker (Recommended for containerization)
A `Dockerfile` is included to serve the application using an Nginx alpine container.

```bash
# Build the Docker image
docker build -t calculator-app -f DockerFile .

# Run the container on port 8080
docker run -d -p 8080:80 calculator-app
```
*Note: Then access it at `http://localhost:8080`*

### 3. Using a Local Python Server
If you have Python installed, you can quickly spin up a local server:

```bash
# Start a local HTTP server
python -m http.server 8080
```
*Note: Then access it at `http://localhost:8080`*

## Technologies Used
- HTML5
- CSS3
- JavaScript (ES6+)
