import matplotlib.pyplot as plt
import numpy as np


class ZoneDrawer:
    """
    Interactive polygon drawer for defining multiple zones on an image.
    Users click vertices; SPACE closes a polygon; Z undoes; ENTER finishes.
    """

    def __init__(self, image: np.ndarray, rect_alpha: float = 0.25, grid_spacing: int = 30):
        """
        :param image: Background image as a NumPy array.
        :param rect_alpha: Transparency for the polygon overlays.
        :param grid_spacing: Spacing in pixels for the grid.
        """
        self.image = image
        self.rect_alpha = rect_alpha
        self.grid_spacing = grid_spacing

        # Internal state
        self.zones = []          # List of polygons (list of (x,y) tuples)
        self._current_pts = []   # Building-up polygon
        self._pt_markers = []    # Scatter markers for vertices
        self._poly_patches = []  # Matplotlib Patch objects for polygons
        self._text_labels = []   # Zone number labels
        self._finished = False  # Flag to know when ENTER was pressed

    def _on_click(self, event):
        """Handle mouse click: add a vertex and draw the edge."""
        if event.inaxes is None or self._finished:
            return
        x, y = event.xdata, event.ydata
        self._current_pts.append((x, y))
        marker = event.inaxes.scatter([x], [y], c='lime', s=50, zorder=5)
        self._pt_markers.append(marker)
        if len(self._current_pts) > 1:
            xs, ys = zip(*self._current_pts)
            event.inaxes.plot(xs, ys, c='lime', alpha=self.rect_alpha, zorder=4)
        plt.draw()

    def _on_key(self, event):
        """Handle key presses: SPACE to close, Z to undo, ENTER to finish."""
        ax = plt.gca()
        if event.key == ' ' and not self._finished:
            if len(self._current_pts) >= 3:
                poly = plt.Polygon(
                    self._current_pts, closed=True, fill=True,
                    edgecolor='lime', facecolor='lime',
                    alpha=self.rect_alpha, zorder=3
                )
                ax.add_patch(poly)
                self._poly_patches.append(poly)

                # label zone
                x0, y0 = self._current_pts[0]
                txt = ax.text(
                    x0 + 10, y0, str(len(self.zones) + 1),
                    color='lime', fontsize=12, weight='bold', zorder=6
                )
                self._text_labels.append(txt)

                # store and clear current
                self.zones.append(self._current_pts.copy())
                for m in self._pt_markers: m.remove()
                self._pt_markers.clear()
                self._current_pts.clear()
                plt.draw()
        elif event.key == 'z' and not self._finished:
            # undo last point or last zone
            if self._current_pts:
                self._pt_markers.pop().remove()
                self._current_pts.pop()
            elif self.zones:
                self.zones.pop()
                self._poly_patches.pop().remove()
                self._text_labels.pop().remove()
            plt.cla()
            self._draw_grid()
            self._redraw_all()
            plt.draw()

        elif event.key in ['enter', 'return']:
            # User finished drawing
            self._finished = True
            plt.close()

    def _redraw_all(self):
        """Redraw background, all polygons, labels, and in-progress shape."""
        ax = plt.gca()
        ax.imshow(self.image)
        for poly in self._poly_patches:
            ax.add_patch(poly)
        for txt in self._text_labels:
            ax.add_artist(txt)
        if len(self._current_pts) > 1:
            xs, ys = zip(*self._current_pts)
            ax.plot(xs, ys, c='lime', alpha=self.rect_alpha, zorder=4)
        for x, y in self._current_pts:
            ax.scatter([x], [y], c='lime', s=50, zorder=5)

    def _draw_grid(self):
        """Draw white dashed grid over the axes."""
        ax = plt.gca()
        h, w = self.image.shape[:2]
        ax.set_xticks(np.arange(0, w + 1, self.grid_spacing))
        ax.set_yticks(np.arange(0, h + 1, self.grid_spacing))
        ax.grid(True, color='white', linestyle='--', linewidth=0.5)

    def start(self, figsize=(8, 6), title="Define zones: SPACE close, Z undo, ENTER finish"):
        """
        Launch the interactive drawer. Blocks until user presses ENTER.
        Returns the list of polygons (each a list of (x,y)).
        """
        # Print a simple console tutorial
        print("\n=== Zone Drawer Quick Tutorial ===")
        print(" 1) Click on the image to add the vertex for a polygon.")
        print(" 2) Press SPACE to close the current polygon.")
        print(" 3) Press 'z' to undo the last point or the last polygon.")
        print(" 4) Press ENTER (or RETURN) to finish drawing all zones and calculate metrics.\n")
        fig, ax = plt.subplots(figsize=figsize)
        ax.imshow(self.image)
        self._draw_grid()
        # reset finish flag before starting
        self._finished = False

        # bind events
        fig.canvas.mpl_connect('button_press_event', self._on_click)
        fig.canvas.mpl_connect('key_press_event', self._on_key)
        ax.set_title(title)
        plt.show()

        return self.zones
