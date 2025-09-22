# jvm_manager.py
import os
import platform
import jpype

class JVMManager:
    _instance = None
    _jvm_started = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JVMManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def start_jvm(cls):
        if cls._jvm_started:
            return True

        try:
            if jpype.isJVMStarted():
                cls._jvm_started = True
                return True

            system = platform.system()
            jvm_args = [
                "-Dlog4j2.loggerContextFactory=org.apache.logging.log4j.simple.SimpleLoggerContextFactory",
                "-Dorg.apache.logging.log4j.simplelog.StatusLogger.level=OFF",
                "-Dlog4j2.level=OFF"
            ]

            if system == "Windows":
                java_home = os.environ.get("JAVA_HOME")
                if not java_home:
                    raise EnvironmentError(
                        "La variable de entorno JAVA_HOME no está configurada."
                    )

                jvm_path = os.path.join(java_home, "bin", "server", "jvm.dll")
                if not os.path.exists(jvm_path):
                    jvm_path = os.path.join(java_home, "bin", "client", "jvm.dll")
                    if not os.path.exists(jvm_path):
                        raise FileNotFoundError("No se encontró jvm.dll")

                jpype.startJVM(jvm_path, *jvm_args)
            else:
                jpype.startJVM(jpype.getDefaultJVMPath(), *jvm_args)

            cls._jvm_started = True
            print("JVM iniciada correctamente.")
            return True

        except Exception as e:
            print(f"Error al iniciar la JVM: {e}")
            return False

    @classmethod
    def is_jvm_started(cls):
        return cls._jvm_started

    @classmethod
    def shutdown(cls):
        if cls._jvm_started and jpype.isJVMStarted():
            try:
                jpype.shutdownJVM()
                cls._jvm_started = False
            except Exception as e:
                print(f"Error al cerrar la JVM: {e}")