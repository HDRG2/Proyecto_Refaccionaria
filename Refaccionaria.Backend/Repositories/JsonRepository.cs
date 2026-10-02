using System.Text.Json;
using System.Threading;

namespace Refaccionaria.Backend.Repositories;

public class JsonRepository<T> : IRepository<T>
    where T : class, IEntity
{
    private readonly string _rutaArchivo;

    public string CarpetaData =>
        Path.GetDirectoryName(_rutaArchivo)
        ?? throw new InvalidOperationException(
            $"No se pudo determinar la carpeta de datos para '{_rutaArchivo}'."
        );

    private List<T> _items = new();

    private bool _cargado = false;

    private readonly SemaphoreSlim _lock =
        new(1, 1);

    
    private const int MAX_RESPALDOS = 10;


    public JsonRepository(string rutaArchivo)
    {
        _rutaArchivo = rutaArchivo;
    }


    // =========================================================
    // CARGAR DATOS
    // =========================================================

    private async Task AsegurarCargadoAsync()
    {
        if (_cargado)
        {
            return;
        }

        await _lock.WaitAsync();

        try
        {
            if (_cargado)
            {
                return;
            }

            if (File.Exists(_rutaArchivo))
            {
                string json =
                    await File.ReadAllTextAsync(
                        _rutaArchivo
                    );

                _items =
                    JsonSerializer.Deserialize<List<T>>(
                        json
                    )
                    ?? new List<T>();


                // =====================================================
                // VALIDAR IDs INVÁLIDOS
                // =====================================================

                var idsInvalidos =
                    _items
                    .Where(x => x.Id <= 0)
                    .Select(x => x.Id)
                    .Distinct()
                    .ToList();

                if (idsInvalidos.Count > 0)
                {
                    throw new InvalidDataException(
                        $"El archivo '{Path.GetFileName(_rutaArchivo)}' " +
                        $"contiene IDs inválidos: " +
                        $"{string.Join(", ", idsInvalidos)}. " +
                        $"Los IDs deben ser mayores que 0."
                    );
                }


                // =====================================================
                // VALIDAR IDs DUPLICADOS
                // =====================================================

                var idsDuplicados =
                    _items
                    .GroupBy(x => x.Id)
                    .Where(grupo => grupo.Count() > 1)
                    .Select(grupo => grupo.Key)
                    .OrderBy(id => id)
                    .ToList();

                if (idsDuplicados.Count > 0)
                {
                    throw new InvalidDataException(
                        $"El archivo '{Path.GetFileName(_rutaArchivo)}' " +
                        $"contiene IDs duplicados: " +
                        $"{string.Join(", ", idsDuplicados)}."
                    );
                }
            }
            else
            {
                _items = new List<T>();
            }

            _cargado = true;
        }
        finally
        {
            _lock.Release();
        }
    }


    // =========================================================
    // CREAR RESPALDO AUTOMÁTICO
    // =========================================================

    private void CrearRespaldo()
    {
        
        if (!File.Exists(_rutaArchivo))
        {
            return;
        }

        string? carpetaData =
            Path.GetDirectoryName(_rutaArchivo);

        if (string.IsNullOrWhiteSpace(carpetaData))
        {
            return;
        }

        string carpetaBackend =
            Directory.GetParent(carpetaData)?.FullName
            ?? carpetaData;

        string nombreArchivo =
            Path.GetFileNameWithoutExtension(
                _rutaArchivo
            );

        string carpetaRespaldos =
            Path.Combine(
                carpetaBackend,
                "Backups",
                "Automaticos",
                nombreArchivo
            );

        Directory.CreateDirectory(
            carpetaRespaldos
        );

        string fecha =
            DateTime.Now.ToString(
                "yyyy-MM-dd_HH-mm-ss-fff"
            );

        string nombreRespaldo =
            $"{nombreArchivo}_{fecha}.json";

        string rutaRespaldo =
            Path.Combine(
                carpetaRespaldos,
                nombreRespaldo
            );

        File.Copy(
            _rutaArchivo,
            rutaRespaldo,
            overwrite: false
        );


        // =====================================================
        // CONSERVAR SOLO LOS ÚLTIMOS 10
        // =====================================================

        var respaldos =
            new DirectoryInfo(carpetaRespaldos)
            .GetFiles("*.json")
            .OrderByDescending(
                archivo =>
                    archivo.CreationTimeUtc
            )
            .ToList();

        foreach (FileInfo respaldo
                 in respaldos.Skip(MAX_RESPALDOS))
        {
            respaldo.Delete();
        }
    }


    // =========================================================
    // CREAR BASE ESTABLE
    // =========================================================

    public static void CrearBaseEstable(
        string carpetaData)
    {
        if (!Directory.Exists(carpetaData))
        {
            throw new DirectoryNotFoundException(
                $"No existe la carpeta de datos: {carpetaData}"
            );
        }

        string carpetaBackend =
            Directory.GetParent(carpetaData)?.FullName
            ?? carpetaData;

        string carpetaBaseEstable =
            Path.Combine(
                carpetaBackend,
                "Backups",
                "BaseEstable"
            );

        Directory.CreateDirectory(
            carpetaBaseEstable
        );

        string[] archivos =
        {
            "autos.json",
            "categorias.json",
            "detalleVentas.json",
            "marcas.json",
            "refacciones.json",
            "usuarios.json",
            "ventas.json"
        };

        foreach (string archivo in archivos)
        {
            string origen =
                Path.Combine(
                    carpetaData,
                    archivo
                );

            if (!File.Exists(origen))
            {
                throw new FileNotFoundException(
                    $"No se encontró {archivo}",
                    origen
                );
            }

            string destino =
                Path.Combine(
                    carpetaBaseEstable,
                    archivo
                );

            File.Copy(
                origen,
                destino,
                overwrite: true
            );
        }
    }

    // =========================================================
    // RESTAURAR ARCHIVO DESDE BASE ESTABLE
    // =========================================================

    public static void RestaurarDesdeBaseEstable(
        string carpetaData,
        string nombreArchivo)
    {
        if (string.IsNullOrWhiteSpace(nombreArchivo))
        {
            throw new ArgumentException(
                "Debe especificarse el archivo que se desea restaurar."
            );
        }

        nombreArchivo = Path.GetFileName(nombreArchivo);

        string[] archivosPermitidos =
        {
        "autos.json",
        "categorias.json",
        "detalleVentas.json",
        "marcas.json",
        "refacciones.json",
        "usuarios.json",
        "ventas.json"
    };

        if (!archivosPermitidos.Contains(
                nombreArchivo,
                StringComparer.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                $"El archivo '{nombreArchivo}' no pertenece " +
                "a los archivos de datos permitidos."
            );
        }

        if (!Directory.Exists(carpetaData))
        {
            throw new DirectoryNotFoundException(
                $"No existe la carpeta de datos: {carpetaData}"
            );
        }

        string carpetaBackend =
            Directory.GetParent(carpetaData)?.FullName
            ?? carpetaData;

        string carpetaBaseEstable =
            Path.Combine(
                carpetaBackend,
                "Backups",
                "BaseEstable"
            );

        string origen =
            Path.Combine(
                carpetaBaseEstable,
                nombreArchivo
            );

        string destino =
            Path.Combine(
                carpetaData,
                nombreArchivo
            );

        if (!File.Exists(origen))
        {
            throw new FileNotFoundException(
                $"No existe una copia estable de '{nombreArchivo}'.",
                origen
            );
        }


        // =====================================================
        // RESPALDAR EL ARCHIVO ACTUAL ANTES DE RESTAURAR
        // =====================================================

        if (File.Exists(destino))
        {
            string nombreSinExtension =
                Path.GetFileNameWithoutExtension(
                    nombreArchivo
                );

            string carpetaAntesRestaurar =
                Path.Combine(
                    carpetaBackend,
                    "Backups",
                    "AntesDeRestaurar",
                    nombreSinExtension
                );

            Directory.CreateDirectory(
                carpetaAntesRestaurar
            );

            string fecha =
                DateTime.Now.ToString(
                    "yyyy-MM-dd_HH-mm-ss-fff"
                );

            string respaldoActual =
                Path.Combine(
                    carpetaAntesRestaurar,
                    $"{nombreSinExtension}_{fecha}.json"
                );

            File.Copy(
                destino,
                respaldoActual,
                overwrite: false
            );
        }


        // =====================================================
        // RESTAURAR ÚNICAMENTE EL ARCHIVO SOLICITADO
        // =====================================================

        File.Copy(
            origen,
            destino,
            overwrite: true
        );
    }

    // =========================================================
    // CREAR RESPALDO TEMPORAL DE TRANSACCIÓN
    // =========================================================

    public static string CrearRespaldoTransaccion(
        string carpetaData)
    {
        if (!Directory.Exists(carpetaData))
        {
            throw new DirectoryNotFoundException(
                $"No existe la carpeta de datos: {carpetaData}"
            );
        }

        string carpetaBackend =
            Directory.GetParent(carpetaData)?.FullName
            ?? carpetaData;

        string idTransaccion =
            DateTime.Now.ToString(
                "yyyy-MM-dd_HH-mm-ss-fff"
            );

        string carpetaTransaccion =
            Path.Combine(
                carpetaBackend,
                "Backups",
                "Transacciones",
                idTransaccion
            );

        Directory.CreateDirectory(
            carpetaTransaccion
        );


        // -----------------------------------------------------
        // ARCHIVOS QUE PARTICIPAN EN UNA VENTA
        // -----------------------------------------------------

        string[] archivos =
        {
        "ventas.json",
        "detalleVentas.json",
        "refacciones.json"
    };


        foreach (string archivo in archivos)
        {
            string origen =
                Path.Combine(
                    carpetaData,
                    archivo
                );

            if (!File.Exists(origen))
            {
                throw new FileNotFoundException(
                    $"No se encontró '{archivo}'.",
                    origen
                );
            }

            string destino =
                Path.Combine(
                    carpetaTransaccion,
                    archivo
                );

            File.Copy(
                origen,
                destino,
                overwrite: true
            );
        }

        return carpetaTransaccion;
    }


    // =========================================================
    // RESTAURAR RESPALDO DE TRANSACCIÓN
    // =========================================================

    public static void RestaurarRespaldoTransaccion(
        string carpetaData,
        string carpetaTransaccion)
    {
        if (!Directory.Exists(carpetaTransaccion))
        {
            throw new DirectoryNotFoundException(
                "No existe el respaldo temporal de la venta."
            );
        }

        string[] archivos =
        {
        "ventas.json",
        "detalleVentas.json",
        "refacciones.json"
    };

        foreach (string archivo in archivos)
        {
            string origen =
                Path.Combine(
                    carpetaTransaccion,
                    archivo
                );

            string destino =
                Path.Combine(
                    carpetaData,
                    archivo
                );

            if (!File.Exists(origen))
            {
                throw new FileNotFoundException(
                    $"El respaldo temporal no contiene '{archivo}'.",
                    origen
                );
            }

            File.Copy(
                origen,
                destino,
                overwrite: true
            );
        }
    }


    // =========================================================
    // ELIMINAR RESPALDO TEMPORAL DE TRANSACCIÓN
    // =========================================================

    public static void EliminarRespaldoTransaccion(
        string carpetaTransaccion)
    {
        if (Directory.Exists(carpetaTransaccion))
        {
            Directory.Delete(
                carpetaTransaccion,
                recursive: true
            );
        }
    }


    // =========================================================
    // GUARDAR DATOS
    // =========================================================

    private async Task GuardarAsync()
    {
        CrearRespaldo();

        var opciones =
            new JsonSerializerOptions
            {
                WriteIndented = true
            };

        string json =
            JsonSerializer.Serialize(
                _items,
                opciones
            );

        await File.WriteAllTextAsync(
            _rutaArchivo,
            json
        );
    }

    // =========================================================
    // RECARGAR ARCHIVO DESDE DISCO
    // =========================================================

    public async Task ReloadAsync()
    {
        await _lock.WaitAsync();

        try
        {
            _cargado = false;
            _items = new List<T>();
        }
        finally
        {
            _lock.Release();
        }

        await AsegurarCargadoAsync();
    }

    // =========================================================
    // OBTENER TODOS
    // =========================================================

    public async Task<IEnumerable<T>> GetAllAsync()
    {
        await AsegurarCargadoAsync();

        return _items;
    }


    // =========================================================
    // OBTENER POR ID
    // =========================================================

    public async Task<T?> GetByIdAsync(int id)
    {
        await AsegurarCargadoAsync();

        return _items.FirstOrDefault(
            x => x.Id == id
        );
    }


    // =========================================================
    // AGREGAR
    // =========================================================

    public async Task AddAsync(T entity)
    {
        await AsegurarCargadoAsync();

        entity.Id =
            _items.Count > 0
                ? _items.Max(x => x.Id) + 1
                : 1;

        _items.Add(entity);

        await GuardarAsync();
    }


    // =========================================================
    // ACTUALIZAR
    // =========================================================

    public async Task UpdateAsync(T entity)
    {
        await AsegurarCargadoAsync();

        int index =
            _items.FindIndex(
                x => x.Id == entity.Id
            );

        if (index == -1)
        {
            return;
        }

        _items[index] = entity;

        await GuardarAsync();
    }


    // =========================================================
    // ELIMINAR
    // =========================================================

    public async Task DeleteAsync(int id)
    {
        await AsegurarCargadoAsync();

        _items.RemoveAll(
            x => x.Id == id
        );

        await GuardarAsync();
    }

    
}