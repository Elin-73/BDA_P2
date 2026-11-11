// Paste this query into Memgraph Lab to add a sample Mendoza real-estate graph.
// It upserts 3 advisors, 6 properties, 6 clients, and their relationships.
// Each client has one creator/responsible advisor and may like several properties.
MERGE (a1:Asesor {id: "a9001"})
SET a1.nombre = "Ana", a1.correo_electronico = "Ana@Mendoza.mx", a1.telefono = "5551009001"
MERGE (a2:Asesor {id: "a9002"})
SET a2.nombre = "Luis", a2.correo_electronico = "Luis@Mendoza.mx", a2.telefono = "5551009002"
MERGE (a3:Asesor {id: "a9003"})
SET a3.nombre = "Marta", a3.correo_electronico = "Marta@Mendoza.mx", a3.telefono = "5551009003"
MERGE (p1:Propiedad {id: "p9001"})
SET p1.direccion = "Calle Cedro 101", p1.precio = 1850000.0, p1.habitaciones = 3, p1.baños = 2, p1.metros_cuadrados = 120.0
MERGE (p2:Propiedad {id: "p9002"})
SET p2.direccion = "Avenida Norte 220", p2.precio = 2350000.0, p2.habitaciones = 4, p2.baños = 3, p2.metros_cuadrados = 165.0
MERGE (p3:Propiedad {id: "p9003"})
SET p3.direccion = "Calle Palma 18", p3.precio = 980000.0, p3.habitaciones = 2, p3.baños = 1, p3.metros_cuadrados = 78.0
MERGE (p4:Propiedad {id: "p9004"})
SET p4.direccion = "Privada del Lago 12", p4.precio = 3100000.0, p4.habitaciones = 4, p4.baños = 3, p4.metros_cuadrados = 210.0
MERGE (p5:Propiedad {id: "p9005"})
SET p5.direccion = "Calle Naranjo 55", p5.precio = 1420000.0, p5.habitaciones = 3, p5.baños = 2, p5.metros_cuadrados = 105.0
MERGE (p6:Propiedad {id: "p9006"})
SET p6.direccion = "Boulevard Central 340", p6.precio = 2750000.0, p6.habitaciones = 3, p6.baños = 2, p6.metros_cuadrados = 155.0
MERGE (a1)-[:ASSIGNED_TO]->(p1)
MERGE (a1)-[:ASSIGNED_TO]->(p2)
MERGE (a2)-[:ASSIGNED_TO]->(p3)
MERGE (a2)-[:ASSIGNED_TO]->(p4)
MERGE (a3)-[:ASSIGNED_TO]->(p5)
MERGE (a3)-[:ASSIGNED_TO]->(p6)
MERGE (c1:Cliente {id: "c9001"})
SET c1.nombre = "Sofia Luna", c1.correo_electronico = "sofia@example.mx", c1.telefono = "5552009001", c1.created_by = a1.id
MERGE (c1)-[:RESPONSIBLE_FOR]->(a1)
MERGE (c1)-[:INTERESTED_IN]->(p1)
MERGE (c1)-[:INTERESTED_IN]->(p2)
MERGE (c2:Cliente {id: "c9002"})
SET c2.nombre = "Diego Cruz", c2.correo_electronico = "diego@example.mx", c2.telefono = "5552009002", c2.created_by = a1.id
MERGE (c2)-[:RESPONSIBLE_FOR]->(a1)
MERGE (c2)-[:INTERESTED_IN]->(p2)
MERGE (c2)-[:INTERESTED_IN]->(p6)
MERGE (c3:Cliente {id: "c9003"})
SET c3.nombre = "Elena Paz", c3.correo_electronico = "elena@example.mx", c3.telefono = "5552009003", c3.created_by = a2.id
MERGE (c3)-[:RESPONSIBLE_FOR]->(a2)
MERGE (c3)-[:INTERESTED_IN]->(p3)
MERGE (c3)-[:INTERESTED_IN]->(p4)
MERGE (c4:Cliente {id: "c9004"})
SET c4.nombre = "Pablo Rey", c4.correo_electronico = "pablo@example.mx", c4.telefono = "5552009004", c4.created_by = a2.id
MERGE (c4)-[:RESPONSIBLE_FOR]->(a2)
MERGE (c4)-[:INTERESTED_IN]->(p4)
MERGE (c4)-[:INTERESTED_IN]->(p5)
MERGE (c5:Cliente {id: "c9005"})
SET c5.nombre = "Lucia Mar", c5.correo_electronico = "lucia@example.mx", c5.telefono = "5552009005", c5.created_by = a3.id
MERGE (c5)-[:RESPONSIBLE_FOR]->(a3)
MERGE (c5)-[:INTERESTED_IN]->(p5)
MERGE (c5)-[:INTERESTED_IN]->(p6)
MERGE (c6:Cliente {id: "c9006"})
SET c6.nombre = "Tomas Rios", c6.correo_electronico = "tomas@example.mx", c6.telefono = "5552009006", c6.created_by = a3.id
MERGE (c6)-[:RESPONSIBLE_FOR]->(a3)
MERGE (c6)-[:INTERESTED_IN]->(p1)
MERGE (c6)-[:INTERESTED_IN]->(p5)
