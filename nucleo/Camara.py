
class Camara:

    def __init__(self, screen_width, screen_height, d=400, z_offset=4.0):
        self.width = screen_width
        self.height = screen_height
        self.d = d                # distancia focal
        self.z_offset = z_offset  # qué tan lejos está el objeto de la cámara

    def proyectar(self, point3d):
        x, y, z = point3d[0], point3d[1], point3d[2]

        z_cam = z + self.z_offset
        if z_cam < 0.1:
            z_cam = 0.1

        x_proj = (x * self.d) / z_cam
        y_proj = (y * self.d) / z_cam

        # Centro de la ventana en pygame (y invertida)
        x_screen = self.width / 2 + x_proj
        y_screen = self.height / 2 - y_proj

        return x_screen, y_screen