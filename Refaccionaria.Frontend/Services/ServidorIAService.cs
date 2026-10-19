
using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

namespace Refaccionaria.Frontend.Services;

public sealed class ServidorIAService
{
    private Process? procesoServidor;

    private bool cierreSolicitado = false;

    private readonly object bloqueoProceso = new();

    private static readonly HttpClient cliente = new()
    {
        Timeout = TimeSpan.FromSeconds(3)
    };

    public async Task IniciarAsync()
    {
        lock (bloqueoProceso)
        {
            if (cierreSolicitado)
                return;
        }

        // Evitar iniciar otro servidor si ya está disponible.
        if (await ServidorDisponibleAsync())
        {
            Debug.WriteLine("IA: FastAPI ya está funcionando.");
            return;
        }

        // Buscar la carpeta principal del proyecto.
        string? carpetaProyecto = BuscarCarpetaProyecto();

        if (carpetaProyecto == null)
        {
            Debug.WriteLine(
                "IA: No se encontró la carpeta del proyecto."
            );
            return;
        }

        // Utilizar exclusivamente el entorno virtual.
        string python = Path.Combine(
            carpetaProyecto,
            ".venv-autogen",
            "Scripts",
            "python.exe"
        );

        if (!File.Exists(python))
        {
            Debug.WriteLine(
                "IA: No se encontró python.exe en .venv-autogen."
            );
            return;
        }

        ProcessStartInfo configuracion = new()
        {
            FileName = python,
            Arguments =
                "-m uvicorn AgenteIA.servidor:app " +
                "--host 127.0.0.1 --port 8000",
            WorkingDirectory = carpetaProyecto,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        try
        {
            Process? procesoIniciado;

            lock (bloqueoProceso)
            {
                if (cierreSolicitado)
                    return;

                procesoServidor = Process.Start(configuracion);
                procesoIniciado = procesoServidor;
            }

            if (procesoIniciado == null)
            {
                Debug.WriteLine(
                    "IA: No se pudo iniciar FastAPI."
                );
                return;
            }

            Debug.WriteLine(
                "IA: Iniciando FastAPI desde .venv-autogen."
            );

            // Esperar hasta aproximadamente 15 segundos.
            for (int intento = 0; intento < 30; intento++)
            {
                lock (bloqueoProceso)
                {
                    if (cierreSolicitado)
                        return;

                    if (procesoIniciado.HasExited)
                    {
                        Debug.WriteLine(
                            "IA: FastAPI terminó durante el arranque."
                        );
                        return;
                    }
                }

                if (await ServidorDisponibleAsync())
                {
                    lock (bloqueoProceso)
                    {
                        if (cierreSolicitado)
                            return;
                    }

                    Debug.WriteLine(
                        "IA: Servidor iniciado correctamente."
                    );
                    return;
                }

                await Task.Delay(500);
            }

            Debug.WriteLine(
                "IA: El servidor no respondió a tiempo."
            );
        }
        catch (Exception ex)
        {
            Debug.WriteLine(
                $"IA: Error al iniciar FastAPI: {ex.Message}"
            );
        }
    }

    private static async Task<bool> ServidorDisponibleAsync()
    {
        try
        {
            using var respuesta = await cliente.GetAsync(
                "http://127.0.0.1:8000/openapi.json"
            );

            return respuesta.IsSuccessStatusCode;
        }
        catch (HttpRequestException)
        {
            return false;
        }
        catch (TaskCanceledException)
        {
            return false;
        }
    }

    private static string? BuscarCarpetaProyecto()
    {
        DirectoryInfo? carpeta = new(
            AppContext.BaseDirectory
        );

        while (carpeta != null)
        {
            string servidor = Path.Combine(
                carpeta.FullName,
                "AgenteIA",
                "servidor.py"
            );

            if (File.Exists(servidor))
                return carpeta.FullName;

            carpeta = carpeta.Parent;
        }

        return null;
    }

    public void Detener()
    {
        lock (bloqueoProceso)
        {
            cierreSolicitado = true;

            if (procesoServidor == null)
                return;

            try
            {
                if (!procesoServidor.HasExited)
                {
                    procesoServidor.Kill(
                        entireProcessTree: true
                    );

                    Debug.WriteLine(
                        "IA: Servidor FastAPI detenido."
                    );
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine(
                    $"IA: Error al detener FastAPI: {ex.Message}"
                );
            }
            finally
            {
                procesoServidor.Dispose();
                procesoServidor = null;
            }
        }
    }
}

