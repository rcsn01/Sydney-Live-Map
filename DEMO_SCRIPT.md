# Sydney Live Map - YouTube Demo Script

**Duration:** ~3-5 minutes  
**Tone:** Professional, technical walkthrough with clear visual demonstrations

---

## Opening (0:00 - 0:30)

**[Screen: VS Code or project folder]**

> "Hey everyone! Today I'm showing you the Sydney Live Map - a real-time interactive web application that visualizes traffic and pedestrian activity across Sydney using live data visualization techniques."

**[Quick transition to browser with app running]**

> "This is a full-stack application built with React, TypeScript, FastAPI, and PostgreSQL, all containerized with Docker. Let me walk you through the key features."

---

## Feature 1: Interactive Map & Real-Time Data (0:30 - 1:15)

**[Screen: Map view with multiple location markers visible]**

> "The core of the application is this interactive map powered by Leaflet. Each circle represents a monitoring location across Sydney - these could be traffic counters, pedestrian sensors, or other data collection points."

**[Hover over a few markers to show tooltips]**

> "As you can see, each location displays its name and current intensity as a percentage. The size and transparency of each circle is dynamically scaled based on the data - larger circles indicate higher activity levels."

**[Pan and zoom the map]**

> "The map is fully interactive - you can pan and zoom freely. Notice how the application only renders markers that are currently visible on screen. This is a key performance optimization."

---

## Feature 2: Type Filtering (1:15 - 2:00)

**[Screen: Focus on the left sidebar with type checkboxes]**

> "On the left sidebar, we have dynamic filtering controls. The application automatically detects all available data types from the database."

**[Click through different type checkboxes]**

> "I can filter by location type - for example, showing only 'all_vehicles' locations, or 'pedestrian' areas. Notice how the map updates in real-time as I toggle these filters."

**[Uncheck all, then check 'unclassified']**

> "Here's where the performance optimizations really shine. When I select a type with many locations and zoom out..."

**[Zoom out to show many markers]**

> "...the application uses canvas rendering instead of SVG. This allows us to display thousands of data points smoothly without freezing the browser. We're also using transparency to reduce visual clutter in dense areas."

---

## Feature 3: Time Travel & Historical Data (2:00 - 3:00)

**[Screen: Focus on Year/Month/Day sliders]**

> "One of the most powerful features is the time-travel capability. Using these date controls, I can view historical snapshots of the data."

**[Adjust year slider]**

> "Let me change the year..."

**[Adjust month slider]**

> "...select a specific month..."

**[Adjust day slider]**

> "...and drill down to a particular day. The entire map updates to show the data as it was at that specific point in time."

**[Show the timestamp display updating]**

> "The selected UTC timestamp is displayed here, and the backend efficiently queries only the most recent data point before this timestamp for each location."

---

## Feature 4: Technical Architecture (3:00 - 3:45)

**[Screen: Split between browser and terminal/Docker Desktop]**

> "From a technical perspective, this is a containerized application with three main services:"

**[Show docker-compose or Docker Desktop]**

> "The PostgreSQL database stores all location and metric data. The FastAPI backend provides a REST API with endpoints for locations, metrics, and filtering. And the React frontend consumes this API to render the interactive experience."

**[Open browser dev tools network tab briefly]**

> "The frontend is optimized to fetch data efficiently - it only requests metrics for locations that are both visible on the map AND match the selected filters. Each location's data is cached client-side to minimize redundant API calls."

---

## Feature 5: Performance Optimizations (3:45 - 4:30)

**[Screen: Back to map with many markers]**

> "Let me highlight the key performance optimizations that make this possible:"

**[Zoom out with many markers visible]**

> "First, viewport-based rendering - only markers within the current map bounds are created. As you pan, markers are added and removed dynamically."

> "Second, canvas rendering instead of SVG - this dramatically reduces DOM overhead when displaying thousands of points."

> "Third, relative scaling - marker sizes are computed based only on the visible set, so the smallest visible location gets the minimum radius, and the largest gets the maximum. This uses a piecewise scaling function that compresses mid-range values while keeping the top-end sensitive."

**[Show the transparency difference]**

> "And finally, transparency - non-selected markers use low opacity to reduce visual clutter while still showing data density."

---

## Closing (4:30 - 5:00)

**[Screen: Map view, possibly zoomed to show Sydney nicely]**

> "So that's the Sydney Live Map - a performant, full-stack web application demonstrating real-time data visualization, historical time-series analysis, and several optimization techniques for handling large datasets in the browser."

**[Optional: Quick flash to code or architecture diagram]**

> "The entire project is containerized and can be deployed with a single Docker Compose command. If you'd like to explore the code or have questions, feel free to leave a comment below."

**[Screen: Fade out or end on map]**

> "Thanks for watching!"

---

## Recording Tips

1. **Preparation:**
   - Clear browser cache and restart Docker containers for a clean demo
   - Have example filters ready (know which types have good data)
   - Set a good initial map zoom/position for Sydney
   - Close unnecessary browser tabs and desktop notifications

2. **Screen recording setup:**
   - Use 1920x1080 resolution
   - Record browser in fullscreen or maximized window
   - Consider using a screen recording tool like OBS Studio
   - Optional: Add cursor highlighting for clarity

3. **Pacing:**
   - Speak clearly and pause slightly between sections
   - Don't rush the interactions - let viewers see the UI respond
   - If something loads slowly, have a prepared comment ready

4. **B-Roll options (optional):**
   - Quick shots of code in VS Code
   - Docker Desktop showing running containers
   - API docs at http://localhost:8000/docs
   - Database query results or table views

5. **Common demo gotchas to avoid:**
   - Make sure Docker is running before you start
   - Check that data is seeded (restart backend if needed)
   - Test your date sliders beforehand - ensure there's data for the dates you select
   - Have a backup plan if the map tiles don't load (internet connection)

---

## Optional Extended Topics (if you want a longer video)

- **Data Import Process:** Show the CSV transformer and import scripts
- **API Walkthrough:** Demonstrate the FastAPI docs interface at /docs
- **Code Deep-Dive:** Walk through a key component like MapView.tsx
- **Deployment:** Show how to deploy on a LAN/server
- **Future Enhancements:** Discuss potential features (clustering, heatmaps, WebGL, etc.)

