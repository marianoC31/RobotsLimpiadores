import math


class OpMat3D:
    
    def __init__(self):
        #Matríz modelado identidad 4x4 3x3 de 3d y 1 por homgenea
        self.reset()
    def reset(self):
        #Reiniciar la matriz de modelado a la identidad
        
        self.M = [
            [1.0,0.0,0.0,0.0],
            [0.0,1.0,0.0,0.0],
            [0.0,0.0,1.0,0.0],
            [0.0,0.0,0.0,1.0]
        ]
    def _mult_matrices(self, A, B):
        
        #Multiplica dos matrices
        C = [[0.0]*4 for _ in range(4)] #crear matriz que guardará la mult
        for i in range(4):
            for j in range(4):
                C[i][j] = sum(A[i][k]* B [k][j] for k in range(4))
                
        return C
    # --- Modo jerárquico (para modelos con partes hijas, como el robot) ---
    # post = False (por defecto): M = T*M  -> comportamiento original (pirámide)
    # post = True:  M = M*T  -> las transformaciones se leen de afuera hacia adentro,
    #                          y push/pop guardan/restauran el "padre".
    post = False

    def _aplicar(self, T):
        if self.post:
            self.M = self._mult_matrices(self.M, T)
        else:
            self.M = self._mult_matrices(T, self.M)

    def push(self):
        if not hasattr(self, "_pila"):
            self._pila = []
        self._pila.append([fila[:] for fila in self.M])

    def pop(self):
        self.M = self._pila.pop()

    def translate(self, tx, ty, tz):
        T = [[1.0,0.0,0.0, tx],
             [0.0,1.0,0.0, ty],
             [0.0,0.0,1.0, tz],
             [0.0,0.0,0.0,1.0]
             ]
        self._aplicar(T)
    def scale(self, sx,sy,sz):
        S = [
            [sx,0.0,0.0,0.0],
            [0.0,sy, 0.0, 0.0],
            [0.0,0.0,sz,0.0],
            [0.0,0.0,0.0,1.0]
        ]
        self._aplicar(S)
    
    def rotate_x(self, deg):
        rad = math.radians(deg)
        c, s = math.cos(rad), math.sin(rad)
        R = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0,   c,  -s, 0.0],
            [0.0,   s,   c, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]
        self._aplicar(R)
    def rotate_y(self, deg):
        rad = math.radians(deg)
        c, s = math.cos(rad), math.sin(rad)
        R = [
            [  c, 0.0,   s, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [ -s, 0.0,   c, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]
        self._aplicar(R)
    def rotate_z(self, deg):
        rad = math.radians(deg)
        c, s = math.cos(rad), math.sin(rad)
        R = [
            [  c,  -s, 0.0, 0.0],
            [  s,   c, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
            ]
        self._aplicar(R)
    
    def transform_points(self, points):
        transformed_points = []
        for p in points:
            x,y,z = p[0], p[1], p[2]
            
            #transformaciój con coords homogeneas
            nx = self.M[0][0]*x + self.M[0][1]*y + self.M[0][2]*z + self.M[0][3]
            ny = self.M[1][0]*x + self.M[1][1]*y + self.M[1][2]*z + self.M[1][3]
            nz = self.M[2][0]*x + self.M[2][1]*y + self.M[2][2]*z + self.M[2][3]
            transformed_points.append([nx, ny, nz])
        return transformed_points