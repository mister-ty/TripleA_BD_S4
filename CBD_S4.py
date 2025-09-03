import streamlit as st
import pandas as pd
from datetime import datetime
import re

st.set_page_config(
    page_title="SQL Avanzado - Base de Datos I",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inicializar_estado():
    if 'ejercicios_completados' not in st.session_state:
        st.session_state.ejercicios_completados = [False] * 5
    
    if 'practica_completada' not in st.session_state:
        st.session_state.practica_completada = [False] * 4
    
    if 'modo_docente' not in st.session_state:
        st.session_state.modo_docente = False
    
    if 'progreso_teoria' not in st.session_state:
        st.session_state.progreso_teoria = {
            'revise_teoria': False,
            'hice_ejercicios': False,
            'consulte_ejemplos': False
        }
    
    if 'codigo_sandbox' not in st.session_state:
        st.session_state.codigo_sandbox = "-- Escribe tu consulta SQL aquí\n"

inicializar_estado()

JOINS_SQL = """-- joins.sql - Ejemplos de JOIN en PostgreSQL
-- Base de Datos I - Semana 4

-- INNER JOIN: Solo registros que coinciden en ambas tablas
SELECT 
    s.nombre AS estudiante,
    c.nombre AS curso,
    e.fecha_inscripcion
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses c ON e.course_id = c.course_id;

-- LEFT JOIN: Todos los estudiantes, incluso sin inscripciones
SELECT 
    s.nombre,
    s.ciudad,
    COUNT(e.enrollment_id) AS cursos_inscritos
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
GROUP BY s.student_id, s.nombre, s.ciudad;

-- RIGHT JOIN: Todos los cursos, incluso sin estudiantes
SELECT 
    c.nombre AS curso,
    c.creditos,
    COUNT(e.student_id) AS estudiantes_inscritos
FROM enrollments e
RIGHT JOIN courses c ON c.course_id = e.course_id
GROUP BY c.course_id, c.nombre, c.creditos;

-- JOIN múltiple con filtros
SELECT 
    s.nombre AS estudiante,
    s.email,
    c.nombre AS curso,
    p.nombre AS profesor
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses c ON e.course_id = c.course_id
INNER JOIN professors p ON c.professor_id = p.professor_id
WHERE s.ciudad = 'Medellín' 
  AND c.creditos >= 3
ORDER BY s.nombre, c.nombre;"""

GROUPBY_SQL = """-- groupby.sql - Ejemplos de GROUP BY y funciones de agregación
-- Base de Datos I - Semana 4

-- COUNT: Contar estudiantes por ciudad
SELECT 
    ciudad,
    COUNT(*) AS total_estudiantes
FROM students
GROUP BY ciudad
ORDER BY total_estudiantes DESC;

-- AVG: Promedio de créditos por departamento
SELECT 
    departamento,
    AVG(creditos) AS promedio_creditos,
    COUNT(*) AS total_cursos
FROM courses
GROUP BY departamento;

-- SUM: Total de créditos por estudiante
SELECT 
    s.nombre,
    SUM(c.creditos) AS creditos_totales
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses c ON e.course_id = c.course_id
GROUP BY s.student_id, s.nombre
HAVING SUM(c.creditos) >= 12;

-- MAX y MIN: Curso con más y menos créditos
SELECT 
    departamento,
    MAX(creditos) AS max_creditos,
    MIN(creditos) AS min_creditos,
    AVG(creditos)::NUMERIC(3,1) AS avg_creditos
FROM courses
GROUP BY departamento
HAVING COUNT(*) > 2;

-- Agregación con múltiples condiciones
SELECT 
    EXTRACT(YEAR FROM fecha_inscripcion) AS año,
    EXTRACT(MONTH FROM fecha_inscripcion) AS mes,
    COUNT(*) AS inscripciones,
    COUNT(DISTINCT student_id) AS estudiantes_unicos
FROM enrollments
GROUP BY año, mes
HAVING COUNT(*) > 5
ORDER BY año DESC, mes DESC;"""

VIEWS_INDEXES_SQL = """-- views_indexes.sql - Ejemplos de vistas e índices
-- Base de Datos I - Semana 4

-- ÍNDICES: Mejoran el rendimiento de consultas

-- Índice simple en columna única
CREATE INDEX idx_students_email 
ON students(email);

-- Índice compuesto
CREATE INDEX idx_enrollments_student_course 
ON enrollments(student_id, course_id);

-- Índice único (garantiza unicidad)
CREATE UNIQUE INDEX idx_students_documento 
ON students(documento);

-- Índice parcial (solo para ciertos registros)
CREATE INDEX idx_active_students 
ON students(ciudad) 
WHERE activo = true;

-- VISTAS: Consultas predefinidas reutilizables

-- Vista simple
CREATE VIEW v_estudiantes_activos AS
SELECT student_id, nombre, email, ciudad
FROM students
WHERE activo = true;

-- Vista con JOIN
CREATE VIEW v_resumen_inscripciones AS
SELECT 
    s.nombre AS estudiante,
    c.nombre AS curso,
    c.creditos,
    e.fecha_inscripcion,
    p.nombre AS profesor
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses c ON e.course_id = c.course_id
INNER JOIN professors p ON c.professor_id = p.professor_id;

-- Vista con agregación
CREATE VIEW v_estadisticas_cursos AS
SELECT 
    c.course_id,
    c.nombre AS curso,
    c.creditos,
    COUNT(e.student_id) AS total_estudiantes,
    p.nombre AS profesor
FROM courses c
LEFT JOIN enrollments e ON c.course_id = e.course_id
LEFT JOIN professors p ON c.professor_id = p.professor_id
GROUP BY c.course_id, c.nombre, c.creditos, p.nombre;

-- Vista materializada (PostgreSQL específico)
CREATE MATERIALIZED VIEW mv_reporte_mensual AS
SELECT 
    DATE_TRUNC('month', fecha_inscripcion) AS mes,
    COUNT(*) AS inscripciones,
    COUNT(DISTINCT student_id) AS estudiantes_unicos,
    COUNT(DISTINCT course_id) AS cursos_diferentes
FROM enrollments
GROUP BY mes
WITH DATA;

-- Refrescar vista materializada
REFRESH MATERIALIZED VIEW mv_reporte_mensual;"""

def aplicar_estilos():
    st.markdown("""
    <style>
    .main {
        background-color: #ffffff;
    }
    
    /* Mejora de contraste para tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f8f9fa;
        border-bottom: 2px solid #dee2e6;
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        color: #2d3748;
        font-weight: 500;
        border: 1px solid #dee2e6;
        border-bottom: none;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f1f5f9;
        color: #1a202c;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4a5568 !important;
        color: #ffffff !important;
        font-weight: 600;
        border-color: #4a5568 !important;
    }
    
    .header-principal {
        background: linear-gradient(135deg, #4a5568 0%, #718096 100%);
        color: white;
        padding: 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    
    .header-principal h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 500;
    }
    
    .concepto-card {
        background: white;
        padding: 1.5rem;
        border-radius: 6px;
        border-left: 3px solid #4a5568;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .concepto-card h4 {
        color: #1a202c;
        font-weight: 600;
    }
    
    .concepto-card p {
        color: #4a5568;
    }
    
    .ejercicio-container {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    .solucion-docente {
        background: #e8f4f8;
        border: 1px solid #2c5282;
        border-radius: 4px;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    .modo-docente-activo {
        background: #fed7aa;
        color: #7c2d12;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 600;
        text-align: center;
        margin: 1rem 0;
    }
    
    .progreso-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 6px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .progreso-card h4 {
        color: #2d3748;
        margin-bottom: 1rem;
    }
    
    .resultado-tabla {
        background: white;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
    }
    
    .tip-box {
        background: #fffbeb;
        border-left: 3px solid #d97706;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
        color: #78350f;
    }
    
    /* Botones con mejor contraste */
    .stButton > button {
        background: #4a5568;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background: #2d3748;
        color: white;
    }
    
    /* Código con fondo claro para mejor legibilidad */
    .stCode, pre {
        background-color: #f7fafc !important;
        color: #1a202c !important;
        border: 1px solid #e2e8f0 !important;
        padding: 1rem !important;
        border-radius: 4px !important;
    }
    
    /* Asegurar buen contraste en todo el texto */
    p, li, span {
        color: #2d3748;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #1a202c;
    }
    
    /* Radio buttons y checkboxes con mejor contraste */
    .stRadio > label {
        color: #2d3748 !important;
    }
    
    .stCheckbox > label {
        color: #2d3748 !important;
    }
    
    /* Expander con mejor contraste */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        color: #1a202c !important;
        border: 1px solid #dee2e6;
    }
    
    /* Info, success, warning, error boxes */
    .stAlert {
        background-color: #f8f9fa;
        color: #1a202c;
        border: 1px solid #cbd5e0;
    }
    </style>
    """, unsafe_allow_html=True)

def validar_sintaxis_sql(codigo):
    codigo = codigo.strip().upper()
    comandos_validos = ['SELECT', 'CREATE', 'INSERT', 'UPDATE', 'DELETE', 'ALTER', 'DROP']
    
    if not codigo:
        return False, "El código está vacío"
    
    primer_comando = codigo.split()[0] if codigo.split() else ""
    if primer_comando in comandos_validos:
        if 'SELECT' in codigo:
            if 'JOIN' in codigo and 'ON' not in codigo:
                return False, "JOIN requiere cláusula ON"
            if 'GROUP BY' in codigo and 'SELECT' in codigo:
                return True, "Consulta con agregación detectada"
        return True, f"Sintaxis válida: {primer_comando}"
    
    return False, "Debe comenzar con un comando SQL válido"

def calcular_progreso_total():
    teoria = sum(st.session_state.progreso_teoria.values())
    ejercicios = sum(st.session_state.ejercicios_completados)
    practica = sum(st.session_state.practica_completada)
    
    total_items = len(st.session_state.progreso_teoria) + \
                  len(st.session_state.ejercicios_completados) + \
                  len(st.session_state.practica_completada)
    
    completados = teoria + ejercicios + practica
    
    return (completados / total_items * 100) if total_items > 0 else 0

def obtener_datos_ejemplo():
    students = pd.DataFrame({
        'student_id': [1, 2, 3, 4, 5],
        'nombre': ['Ana García', 'Luis Pérez', 'María López', 'Carlos Ruiz', 'Laura Torres'],
        'email': ['ana@uni.edu', 'luis@uni.edu', 'maria@uni.edu', 'carlos@uni.edu', 'laura@uni.edu'],
        'ciudad': ['Medellín', 'Bogotá', 'Medellín', 'Cali', 'Medellín']
    })
    
    courses = pd.DataFrame({
        'course_id': [101, 102, 103, 104],
        'nombre': ['Base de Datos I', 'Programación II', 'Cálculo I', 'Física I'],
        'creditos': [4, 3, 4, 3],
        'departamento': ['Sistemas', 'Sistemas', 'Matemáticas', 'Física']
    })
    
    enrollments = pd.DataFrame({
        'enrollment_id': [1, 2, 3, 4, 5, 6, 7],
        'student_id': [1, 1, 2, 2, 3, 4, 5],
        'course_id': [101, 102, 101, 103, 102, 101, 104],
        'fecha_inscripcion': ['2025-01-15', '2025-01-15', '2025-01-16', 
                              '2025-01-16', '2025-01-17', '2025-01-17', '2025-01-18']
    })
    
    return students, courses, enrollments

def vista_inicio():
    st.markdown("""
    <div class="header-principal">
        <h1>Semana 4 – Consultas SQL Avanzadas</h1>
        <p style="margin-top: 0.5rem; font-size: 1.1rem;">Base de Datos I | Universidad Digital</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Objetivos de Aprendizaje
        
        Esta semana profundizaremos en las capacidades avanzadas de SQL para:
        - Combinar datos de múltiples tablas mediante JOIN
        - Generar reportes complejos con funciones de agregación
        - Optimizar consultas mediante índices estratégicos
        - Crear vistas para simplificar consultas recurrentes
        """)
        
        st.markdown("""
        ### Logros Esperados
        
        Al completar esta semana serás capaz de:
        - Escribir consultas con INNER JOIN, LEFT JOIN y RIGHT JOIN
        - Usar GROUP BY y HAVING para análisis de datos
        - Aplicar funciones de agregación (COUNT, SUM, AVG, MAX, MIN)
        - Crear índices para optimizar el rendimiento
        - Diseñar vistas para encapsular lógica compleja
        - Ordenar resultados con ORDER BY múltiple
        """)
    
    with col2:
        st.markdown("""
        <div class="progreso-card">
        <h4>Tu Progreso</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.progreso_teoria['revise_teoria'] = st.checkbox(
            "✓ Revisé la teoría",
            value=st.session_state.progreso_teoria['revise_teoria']
        )
        
        st.session_state.progreso_teoria['hice_ejercicios'] = st.checkbox(
            "✓ Hice los ejercicios",
            value=st.session_state.progreso_teoria['hice_ejercicios']
        )
        
        st.session_state.progreso_teoria['consulte_ejemplos'] = st.checkbox(
            "✓ Consulté ejemplos",
            value=st.session_state.progreso_teoria['consulte_ejemplos']
        )
        
        progreso = calcular_progreso_total()
        st.progress(progreso / 100)
        st.caption(f"Progreso total: {progreso:.0f}%")
    
    if st.session_state.modo_docente:
        st.markdown("""
        <div class="modo-docente-activo">
        MODO DOCENTE ACTIVO - Las soluciones están visibles
        </div>
        """, unsafe_allow_html=True)

def vista_conceptos():
    st.markdown("## Conceptos Clave")
    
    tabs = st.tabs(["JOIN", "ORDER BY", "Funciones de Agregación", "GROUP BY/HAVING", "Índices", "Vistas"])
    
    with tabs[0]:
        st.markdown("""
        ### JOIN - Combinando Tablas
        
        Los JOIN permiten combinar filas de dos o más tablas basándose en columnas relacionadas.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="concepto-card">
            <h4>INNER JOIN</h4>
            <p>Retorna solo los registros que tienen coincidencias en ambas tablas.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.code("""
-- INNER JOIN básico
SELECT s.nombre, c.nombre AS curso
FROM students s
INNER JOIN enrollments e 
    ON s.student_id = e.student_id
INNER JOIN courses c 
    ON e.course_id = c.course_id;""", language='sql')
        
        with col2:
            st.markdown("""
            <div class="concepto-card">
            <h4>LEFT JOIN</h4>
            <p>Retorna todos los registros de la tabla izquierda, incluso sin coincidencias.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.code("""
-- LEFT JOIN para incluir todos
SELECT s.nombre, 
       COUNT(e.enrollment_id) AS cursos
FROM students s
LEFT JOIN enrollments e 
    ON s.student_id = e.student_id
GROUP BY s.student_id, s.nombre;""", language='sql')
        
        if st.checkbox("Ver ejemplo con datos", key="join_ejemplo"):
            students, courses, enrollments = obtener_datos_ejemplo()
            
            st.markdown("**Tabla students:**")
            st.dataframe(students.head(3), use_container_width=True)
            
            st.markdown("**Resultado del INNER JOIN:**")
            resultado = pd.DataFrame({
                'estudiante': ['Ana García', 'Ana García', 'Luis Pérez'],
                'curso': ['Base de Datos I', 'Programación II', 'Base de Datos I']
            })
            st.dataframe(resultado, use_container_width=True)
    
    with tabs[1]:
        st.markdown("""
        ### ORDER BY - Ordenamiento de Resultados
        
        ORDER BY permite ordenar los resultados por una o más columnas.
        """)
        
        st.code("""
-- Ordenamiento simple
SELECT nombre, ciudad 
FROM students 
ORDER BY ciudad ASC, nombre DESC;

-- Ordenamiento con expresiones
SELECT nombre, 
       ciudad,
       LENGTH(nombre) AS longitud_nombre
FROM students 
ORDER BY longitud_nombre DESC, ciudad;

-- Ordenamiento con NULLS FIRST/LAST
SELECT nombre, fecha_nacimiento
FROM students
ORDER BY fecha_nacimiento DESC NULLS LAST;""", language='sql')
    
    with tabs[2]:
        st.markdown("""
        ### Funciones de Agregación
        
        Las funciones de agregación realizan cálculos sobre conjuntos de valores.
        """)
        
        funciones = {
            'Función': ['COUNT()', 'SUM()', 'AVG()', 'MAX()', 'MIN()'],
            'Descripción': [
                'Cuenta el número de filas',
                'Suma los valores',
                'Calcula el promedio',
                'Obtiene el valor máximo',
                'Obtiene el valor mínimo'
            ],
            'Ejemplo': [
                'COUNT(*) o COUNT(columna)',
                'SUM(creditos)',
                'AVG(calificacion)',
                'MAX(fecha)',
                'MIN(precio)'
            ]
        }
        st.table(pd.DataFrame(funciones))
        
        st.code("""
-- Ejemplos de funciones de agregación
SELECT 
    COUNT(*) AS total_estudiantes,
    COUNT(DISTINCT ciudad) AS ciudades_diferentes,
    AVG(edad)::NUMERIC(4,2) AS edad_promedio,
    MAX(fecha_ingreso) AS ultimo_ingreso,
    MIN(fecha_ingreso) AS primer_ingreso
FROM students
WHERE activo = true;""", language='sql')
    
    with tabs[3]:
        st.markdown("""
        ### GROUP BY y HAVING
        
        GROUP BY agrupa filas con valores idénticos en columnas especificadas.
        HAVING filtra grupos después de la agregación.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**GROUP BY**")
            st.code("""
-- Agrupar por ciudad
SELECT ciudad, 
       COUNT(*) AS estudiantes
FROM students
GROUP BY ciudad
ORDER BY estudiantes DESC;""", language='sql')
        
        with col2:
            st.markdown("**HAVING**")
            st.code("""
-- Filtrar grupos con HAVING
SELECT ciudad, 
       COUNT(*) AS estudiantes
FROM students
GROUP BY ciudad
HAVING COUNT(*) > 2
ORDER BY estudiantes DESC;""", language='sql')
        
        st.info("**Tip:** WHERE filtra filas ANTES de agrupar, HAVING filtra grupos DESPUÉS de agrupar.")
    
    with tabs[4]:
        st.markdown("""
        ### Índices - Optimización de Consultas
        
        Los índices mejoran significativamente el rendimiento de las consultas.
        """)
        
        st.code("""
-- Índice simple
CREATE INDEX idx_students_email ON students(email);

-- Índice compuesto
CREATE INDEX idx_enrollments_composite 
ON enrollments(student_id, course_id);

-- Índice único
CREATE UNIQUE INDEX idx_documento 
ON students(documento);

-- Índice parcial
CREATE INDEX idx_active_students 
ON students(ciudad) 
WHERE activo = true;

-- Eliminar índice
DROP INDEX idx_students_email;""", language='sql')
        
        st.warning("**Importante:** Los índices aceleran las consultas pero ralentizan INSERT/UPDATE/DELETE.")
    
    with tabs[5]:
        st.markdown("""
        ### Vistas - Consultas Reutilizables
        
        Las vistas son consultas almacenadas que se comportan como tablas virtuales.
        """)
        
        st.code("""
-- Crear vista simple
CREATE VIEW v_estudiantes_activos AS
SELECT student_id, nombre, email, ciudad
FROM students
WHERE activo = true;

-- Vista con JOIN
CREATE VIEW v_inscripciones_detalle AS
SELECT 
    s.nombre AS estudiante,
    c.nombre AS curso,
    c.creditos,
    e.fecha_inscripcion
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id;

-- Usar la vista
SELECT * FROM v_estudiantes_activos
WHERE ciudad = 'Medellín';

-- Eliminar vista
DROP VIEW v_estudiantes_activos;""", language='sql')
        
        st.success("**Beneficios:** Simplifican consultas complejas, mejoran seguridad y mantienen consistencia.")

def vista_ejercicios():
    st.markdown("## Ejercicios Guiados")
    
    ejercicios = [
        {
            'titulo': 'Ejercicio 1: JOIN entre students y courses',
            'enunciado': 'Escribe una consulta que liste todos los estudiantes con sus cursos inscritos, mostrando nombre del estudiante, curso y créditos.',
            'pista': 'Necesitas hacer JOIN entre 3 tablas: students, enrollments y courses.',
            'plantilla': """-- Lista estudiantes con sus cursos
SELECT 
    -- Completa las columnas
FROM students s
-- Agrega los JOIN necesarios
""",
            'solucion': """SELECT 
    s.nombre AS estudiante,
    c.nombre AS curso,
    c.creditos
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses c ON e.course_id = c.course_id
ORDER BY s.nombre, c.nombre;"""
        },
        {
            'titulo': 'Ejercicio 2: COUNT con GROUP BY',
            'enunciado': 'Cuenta cuántos estudiantes hay por cada ciudad.',
            'pista': 'Usa GROUP BY con la columna ciudad y COUNT(*) para contar.',
            'plantilla': """-- Contar estudiantes por ciudad
SELECT 
    -- Completa aquí
FROM students
-- Agrupa por...
""",
            'solucion': """SELECT 
    ciudad,
    COUNT(*) AS total_estudiantes
FROM students
GROUP BY ciudad
ORDER BY total_estudiantes DESC;"""
        },
        {
            'titulo': 'Ejercicio 3: AVG de créditos',
            'enunciado': 'Calcula el promedio de créditos por departamento.',
            'pista': 'Agrupa por departamento y usa AVG() en créditos.',
            'plantilla': """-- Promedio de créditos por departamento
SELECT 
    departamento,
    -- Calcula el promedio aquí
FROM courses
-- Agrupa por...
""",
            'solucion': """SELECT 
    departamento,
    AVG(creditos)::NUMERIC(3,1) AS promedio_creditos,
    COUNT(*) AS total_cursos
FROM courses
GROUP BY departamento
ORDER BY promedio_creditos DESC;"""
        },
        {
            'titulo': 'Ejercicio 4: HAVING para filtrar grupos',
            'enunciado': 'Encuentra las ciudades que tienen más de 2 estudiantes.',
            'pista': 'Usa GROUP BY ciudad y HAVING COUNT(*) > 2.',
            'plantilla': """-- Ciudades con más de 2 estudiantes
SELECT 
    ciudad,
    COUNT(*) AS estudiantes
FROM students
GROUP BY ciudad
-- Filtra los grupos aquí
""",
            'solucion': """SELECT 
    ciudad,
    COUNT(*) AS estudiantes
FROM students
GROUP BY ciudad
HAVING COUNT(*) > 2
ORDER BY estudiantes DESC;"""
        },
        {
            'titulo': 'Ejercicio 5: Crear vista ResumenInscripciones',
            'enunciado': 'Crea una vista que muestre estudiante, curso y fecha de inscripción.',
            'pista': 'CREATE VIEW con SELECT y los JOIN necesarios.',
            'plantilla': """-- Crear vista de resumen
CREATE VIEW v_resumen_inscripciones AS
-- Completa la consulta SELECT
""",
            'solucion': """CREATE VIEW v_resumen_inscripciones AS
SELECT 
    s.nombre AS estudiante,
    c.nombre AS curso,
    e.fecha_inscripcion,
    c.creditos
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses c ON e.course_id = c.course_id;"""
        }
    ]
    
    for i, ejercicio in enumerate(ejercicios):
        with st.container():
            col1, col2 = st.columns([10, 1])
            
            with col1:
                st.markdown(f"### {ejercicio['titulo']}")
            
            with col2:
                st.session_state.ejercicios_completados[i] = st.checkbox(
                    "✓",
                    key=f"ej_{i}",
                    value=st.session_state.ejercicios_completados[i]
                )
            
            st.markdown(f"**Enunciado:** {ejercicio['enunciado']}")
            
            with st.expander("Ver pista"):
                st.info(ejercicio['pista'])
            
            codigo = st.text_area(
                "Tu solución:",
                value=ejercicio['plantilla'],
                height=120,
                key=f"codigo_{i}"
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"Validar", key=f"val_{i}"):
                    valido, mensaje = validar_sintaxis_sql(codigo)
                    if valido:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
            
            with col2:
                if st.button(f"Ver resultado simulado", key=f"res_{i}"):
                    if i == 0:
                        resultado = pd.DataFrame({
                            'estudiante': ['Ana García', 'Ana García', 'Luis Pérez'],
                            'curso': ['Base de Datos I', 'Programación II', 'Base de Datos I'],
                            'creditos': [4, 3, 4]
                        })
                        st.dataframe(resultado, use_container_width=True)
                    elif i == 1:
                        resultado = pd.DataFrame({
                            'ciudad': ['Medellín', 'Bogotá', 'Cali'],
                            'total_estudiantes': [3, 1, 1]
                        })
                        st.dataframe(resultado, use_container_width=True)
            
            with col3:
                if st.session_state.modo_docente:
                    if st.button(f"Mostrar solución", key=f"sol_{i}"):
                        st.code(ejercicio['solucion'], language='sql')
                else:
                    st.info("Activa modo docente para ver solución")
            
            st.divider()
    
    completados = sum(st.session_state.ejercicios_completados)
    total = len(ejercicios)
    
    if completados == total:
        st.success(f"Excelente! Completaste todos los ejercicios ({completados}/{total})")
    else:
        st.info(f"Progreso: {completados}/{total} ejercicios completados")

def vista_sandbox():
    st.markdown("## Práctica Autónoma (Sandbox)")
    
    st.markdown("Practica con estos retos avanzados. Haz clic para cargar el código base.")
    
    retos = [
        {
            'titulo': 'JOIN de 3 tablas',
            'descripcion': 'Combina students, courses y enrollments',
            'codigo': """-- JOIN múltiple
SELECT 
    s.nombre AS estudiante,
    s.ciudad,
    c.nombre AS curso,
    c.creditos,
    e.fecha_inscripcion
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses c ON e.course_id = c.course_id
WHERE c.creditos >= 3
ORDER BY s.nombre, c.nombre;"""
        },
        {
            'titulo': 'ORDER BY múltiple',
            'descripcion': 'Ordena por apellido y nombre',
            'codigo': """-- Ordenamiento múltiple
SELECT 
    SPLIT_PART(nombre, ' ', 2) AS apellido,
    SPLIT_PART(nombre, ' ', 1) AS primer_nombre,
    ciudad,
    email
FROM students
ORDER BY apellido ASC, primer_nombre ASC;"""
        },
        {
            'titulo': 'Índice en email',
            'descripcion': 'Crea un índice único en la columna email',
            'codigo': """-- Índice único para email
CREATE UNIQUE INDEX idx_students_email 
ON students(LOWER(email));

-- Verificar índices existentes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'students';"""
        },
        {
            'titulo': 'Vista con agregación',
            'descripcion': 'Vista que cuenta cursos por profesor',
            'codigo': """-- Vista con conteo de cursos
CREATE VIEW v_profesor_estadisticas AS
SELECT 
    p.nombre AS profesor,
    p.departamento,
    COUNT(c.course_id) AS total_cursos,
    SUM(c.creditos) AS total_creditos,
    AVG(c.creditos)::NUMERIC(3,1) AS promedio_creditos
FROM professors p
LEFT JOIN courses c ON p.professor_id = c.professor_id
GROUP BY p.professor_id, p.nombre, p.departamento;

-- Usar la vista
SELECT * FROM v_profesor_estadisticas
WHERE total_cursos > 0
ORDER BY total_cursos DESC;"""
        }
    ]
    
    cols = st.columns(4)
    for i, reto in enumerate(retos):
        with cols[i]:
            if st.button(reto['titulo'], key=f"reto_{i}"):
                st.session_state.codigo_sandbox = reto['codigo']
                st.rerun()
            
            st.session_state.practica_completada[i] = st.checkbox(
                "✓ Hecho",
                key=f"prac_{i}",
                value=st.session_state.practica_completada[i]
            )
    
    codigo = st.text_area(
        "Editor SQL:",
        value=st.session_state.codigo_sandbox,
        height=250,
        key="sandbox"
    )
    st.session_state.codigo_sandbox = codigo
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Validar sintaxis"):
            valido, mensaje = validar_sintaxis_sql(codigo)
            if valido:
                st.success(mensaje)
            else:
                st.warning(mensaje)
    
    with col2:
        if st.button("Limpiar"):
            st.session_state.codigo_sandbox = "-- Escribe tu consulta SQL aquí\n"
            st.rerun()
    
    with col3:
        if st.button("Copiar"):
            st.info("Selecciona el texto y copia con Ctrl+C")
    
    with st.expander("Ver descripción detallada de los retos"):
        for reto in retos:
            st.markdown(f"**{reto['titulo']}**")
            st.markdown(f"*{reto['descripcion']}*")
            st.code(reto['codigo'], language='sql')
    
    st.markdown("""
    <div class="tip-box">
    <strong>Tips de Buenas Prácticas:</strong>
    <ul>
    <li>Evita SELECT * en producción, especifica las columnas necesarias</li>
    <li>Usa alias descriptivos para mejorar la legibilidad</li>
    <li>Siempre incluye ORDER BY para resultados consistentes</li>
    <li>Considera índices en columnas frecuentemente filtradas o usadas en JOIN</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

def vista_cheatsheet():
    st.markdown("## Cheat-sheet SQL Avanzado")
    
    comandos = pd.DataFrame({
        'Comando': [
            'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN',
            'GROUP BY', 'HAVING', 'ORDER BY',
            'COUNT()', 'SUM()', 'AVG()', 'MAX()', 'MIN()',
            'CREATE INDEX', 'CREATE VIEW', 'CREATE MATERIALIZED VIEW'
        ],
        'Categoría': [
            'JOIN', 'JOIN', 'JOIN',
            'Agrupación', 'Filtro de grupos', 'Ordenamiento',
            'Agregación', 'Agregación', 'Agregación', 'Agregación', 'Agregación',
            'Índice', 'Vista', 'Vista'
        ],
        'Descripción': [
            'Une tablas con registros coincidentes',
            'Todos de la izquierda + coincidentes',
            'Todos de la derecha + coincidentes',
            'Agrupa filas por columnas',
            'Filtra grupos después de agrupar',
            'Ordena resultados',
            'Cuenta registros',
            'Suma valores',
            'Calcula promedio',
            'Valor máximo',
            'Valor mínimo',
            'Crea índice para optimización',
            'Crea vista (consulta almacenada)',
            'Vista con datos materializados'
        ]
    })
    
    st.dataframe(comandos, use_container_width=True)
    
    st.markdown("### Ejemplos Rápidos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Consulta con JOIN y agregación:**")
        st.code("""
SELECT 
    s.ciudad,
    COUNT(DISTINCT s.student_id) AS estudiantes,
    COUNT(e.enrollment_id) AS inscripciones
FROM students s
LEFT JOIN enrollments e 
    ON s.student_id = e.student_id
GROUP BY s.ciudad
HAVING COUNT(DISTINCT s.student_id) > 1
ORDER BY estudiantes DESC;""", language='sql')
    
    with col2:
        st.markdown("**Vista con múltiples JOIN:**")
        st.code("""
CREATE VIEW v_reporte_completo AS
SELECT 
    s.nombre AS estudiante,
    c.nombre AS curso,
    p.nombre AS profesor,
    c.creditos,
    e.fecha_inscripcion
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
JOIN courses c ON e.course_id = c.course_id
JOIN professors p ON c.professor_id = p.professor_id;""", language='sql')

def vista_recursos():
    st.markdown("## Recursos Adicionales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Archivos SQL")
        
        st.download_button(
            label="Descargar joins.sql",
            data=JOINS_SQL,
            file_name="joins.sql",
            mime="text/plain"
        )
        
        st.download_button(
            label="Descargar groupby.sql",
            data=GROUPBY_SQL,
            file_name="groupby.sql",
            mime="text/plain"
        )
        
        st.download_button(
            label="Descargar views_indexes.sql",
            data=VIEWS_INDEXES_SQL,
            file_name="views_indexes.sql",
            mime="text/plain"
        )
    
    with col2:
        st.markdown("### Referencias Bibliográficas")
        
        st.markdown("""
        - **Marqués, M. (2009).** *Bases de datos.* 
          Castelló de la Plana: UJI.
          
        - **Pulido Romero, E. et al. (2019).** 
          *Base de datos.* México: Grupo Patria.
          
        - **PostgreSQL Documentation (2025).** 
          *Official PostgreSQL 17 Documentation.*
        """)
    
    with col3:
        st.markdown("### Enlaces Útiles")
        
        st.markdown("""
        - [PostgreSQL JOIN Tutorial](https://www.postgresql.org/docs/current/tutorial-join.html)
        - [SQL Aggregate Functions](https://www.postgresql.org/docs/current/functions-aggregate.html)
        - [Index Types in PostgreSQL](https://www.postgresql.org/docs/current/indexes-types.html)
        - [Views Documentation](https://www.postgresql.org/docs/current/sql-createview.html)
        """)
    
    st.divider()
    
    st.info("""
    **Recomendación de estudio:** 
    Practica primero con JOINs simples antes de combinar con GROUP BY. 
    Los índices son cruciales para rendimiento en tablas grandes.
    Las vistas simplifican consultas complejas recurrentes.
    """)

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <div style="background: #4a5568;
                    width: 60px; height: 60px; border-radius: 8px;
                    margin: 0 auto; display: flex; align-items: center;
                    justify-content: center; color: white; font-size: 1.5rem;">
            🗄️
        </div>
        <h3 style="margin-top: 1rem;">Base de Datos I</h3>
        <p style="color: #718096;">Semana 4 - SQL Avanzado</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### Navegación")
    pagina = st.radio(
        "Selecciona sección:",
        ["Inicio", "Conceptos", "Ejercicios", "Práctica", "Cheat-sheet", "Recursos"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    st.markdown("### Configuración")
    st.session_state.modo_docente = st.toggle(
        "Modo Docente",
        value=st.session_state.modo_docente,
        help="Activa para ver soluciones"
    )
    
    if st.session_state.modo_docente:
        st.warning("**Modo Docente Activo**")
    
    st.divider()
    
    st.markdown("### Progreso General")
    progreso = calcular_progreso_total()
    st.progress(progreso / 100)
    st.caption(f"{progreso:.0f}% completado")
    
    with st.expander("Detalles"):
        teoria = sum(st.session_state.progreso_teoria.values())
        ejercicios = sum(st.session_state.ejercicios_completados)
        practica = sum(st.session_state.practica_completada)
        
        st.caption(f"Teoría: {teoria}/3")
        st.caption(f"Ejercicios: {ejercicios}/5")
        st.caption(f"Práctica: {practica}/4")
    
    st.divider()
    
    if st.button("Reiniciar Progreso"):
        if st.checkbox("Confirmar"):
            for key in ['ejercicios_completados', 'practica_completada', 
                       'progreso_teoria', 'codigo_sandbox']:
                if key in st.session_state:
                    if key == 'codigo_sandbox':
                        st.session_state[key] = "-- Escribe tu consulta SQL aquí\n"
                    else:
                        st.session_state[key] = {k: False for k in st.session_state[key]} \
                                               if isinstance(st.session_state[key], dict) \
                                               else [False] * len(st.session_state[key])
            st.success("Progreso reiniciado")
            st.rerun()

aplicar_estilos()

if pagina == "Inicio":
    vista_inicio()
elif pagina == "Conceptos":
    vista_conceptos()
elif pagina == "Ejercicios":
    vista_ejercicios()
elif pagina == "Práctica":
    vista_sandbox()
elif pagina == "Cheat-sheet":
    vista_cheatsheet()
elif pagina == "Recursos":
    vista_recursos()

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #718096; padding: 2rem;">
    <p>SQL Avanzado - Base de Datos I | Universidad Digital | 2025</p>
    <p style="font-size: 0.9rem;">Material educativo para consultas SQL complejas</p>
</div>
""", unsafe_allow_html=True)