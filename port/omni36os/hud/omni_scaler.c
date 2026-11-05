/* Hook EGL / OpenGL ES do scaler nativo do Omni36OS para R36S (Mali-G31).
 * Implementa pipeline espacial leve (AMD CAS e Sharp Bilinear) e Frame Pacing.
 * Desativado por padrão; habilitável por perfil ou variáveis de ambiente.
 */
typedef unsigned long size_t;
typedef long ssize_t;
typedef int GLint;
typedef unsigned int GLuint;
typedef unsigned int GLenum;
typedef unsigned char GLboolean;
typedef float GLfloat;

struct timespec {
    long tv_sec;
    long tv_nsec;
};

extern void *dlopen(const char *, int);
extern void *dlvsym(void *, const char *, const char *);
extern char *getenv(const char *);
extern int strcmp(const char *, const char *);
extern int strncmp(const char *, const char *, size_t);
extern int open(const char *, int, ...);
extern ssize_t read(int, void *, size_t);
extern ssize_t write(int, const void *, size_t);
extern int close(int);

#define RTLD_LAZY 1
#define RTLD_NEXT ((void *)-1l)
#define RTLD_DEFAULT ((void *)0)
#define O_RDONLY 0
#define O_WRONLY 1
#define O_CREAT 0100
#define O_TRUNC 01000
#define O_APPEND 02000
#define O_CLOEXEC 02000000
#define CLOCK_MONOTONIC 1

#define GL_FRAGMENT_SHADER 0x8B30
#define GL_VERTEX_SHADER 0x8B31
#define GL_COMPILE_STATUS 0x8B81
#define GL_LINK_STATUS 0x8B82
#define GL_CURRENT_PROGRAM 0x8B8D
#define GL_ARRAY_BUFFER 0x8892
#define GL_ARRAY_BUFFER_BINDING 0x8894
#define GL_FRAMEBUFFER 0x8D40
#define GL_FRAMEBUFFER_BINDING 0x8CA6
#define GL_TEXTURE_2D 0x0DE1
#define GL_TEXTURE_BINDING_2D 0x8069
#define GL_TEXTURE0 0x84C0
#define GL_ACTIVE_TEXTURE 0x84E0
#define GL_TEXTURE_MIN_FILTER 0x2801
#define GL_TEXTURE_MAG_FILTER 0x2800
#define GL_TEXTURE_WRAP_S 0x2802
#define GL_TEXTURE_WRAP_T 0x2803
#define GL_LINEAR 0x2601
#define GL_CLAMP_TO_EDGE 0x812F
#define GL_RGB 0x1907
#define GL_UNSIGNED_BYTE 0x1401
#define GL_FLOAT 0x1406
#define GL_TRIANGLE_STRIP 0x0005
#define GL_VIEWPORT 0x0BA2
#define GL_BLEND 0x0BE2
#define GL_DEPTH_TEST 0x0B71
#define GL_SCISSOR_TEST 0x0C11
#define GL_CULL_FACE 0x0B44
#define GL_STENCIL_TEST 0x0B90
#define GL_COLOR_WRITEMASK 0x0C23
#define GL_BLEND_SRC_RGB 0x80C9
#define GL_BLEND_DST_RGB 0x80C8
#define GL_BLEND_SRC_ALPHA 0x80CB
#define GL_BLEND_DST_ALPHA 0x80CA
#define GL_BLEND_EQUATION_RGB 0x8009
#define GL_BLEND_EQUATION_ALPHA 0x883D
#define GL_VERTEX_ARRAY_BINDING 0x85B5
#define GL_VERTEX_ATTRIB_ARRAY_ENABLED 0x8622
#define GL_VERTEX_ATTRIB_ARRAY_SIZE 0x8623
#define GL_VERTEX_ATTRIB_ARRAY_TYPE 0x8625
#define GL_VERTEX_ATTRIB_ARRAY_NORMALIZED 0x886A
#define GL_VERTEX_ATTRIB_ARRAY_STRIDE 0x8624
#define GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING 0x889F
#define GL_VERTEX_ATTRIB_ARRAY_POINTER 0x8645

typedef void *(*dlsym_fn)(void *, const char *);
typedef unsigned (*swap_fn)(void *, void *);
typedef void *(*gpa_fn)(const char *);
typedef void *(*get_context_fn)(void);
typedef unsigned (*query_surface_fn)(void *, void *, int, int *);
typedef int (*clock_gettime_fn)(int, struct timespec *);
typedef int (*nanosleep_fn)(const struct timespec *, struct timespec *);

/* Ponteiros GL */
typedef GLuint (*glCreateShader_fn)(GLenum);
typedef void (*glShaderSource_fn)(GLuint, GLint, const char **, const GLint *);
typedef void (*glCompileShader_fn)(GLuint);
typedef void (*glGetShaderiv_fn)(GLuint, GLenum, GLint *);
typedef void (*glDeleteShader_fn)(GLuint);
typedef GLuint (*glCreateProgram_fn)(void);
typedef void (*glAttachShader_fn)(GLuint, GLuint);
typedef void (*glBindAttribLocation_fn)(GLuint, GLuint, const char *);
typedef void (*glLinkProgram_fn)(GLuint);
typedef void (*glGetProgramiv_fn)(GLuint, GLenum, GLint *);
typedef void (*glUseProgram_fn)(GLuint);
typedef GLint (*glGetUniformLocation_fn)(GLuint, const char *);
typedef void (*glUniform1i_fn)(GLint, GLint);
typedef void (*glUniform1f_fn)(GLint, float);
typedef void (*glUniform2f_fn)(GLint, float, float);
typedef void (*glGenTextures_fn)(GLint, GLuint *);
typedef void (*glDeleteTextures_fn)(GLint, const GLuint *);
typedef void (*glBindTexture_fn)(GLenum, GLuint);
typedef void (*glTexParameteri_fn)(GLenum, GLenum, GLint);
typedef void (*glTexImage2D_fn)(GLenum, GLint, GLint, GLint, GLint, GLint, GLenum, GLenum, const void *);
typedef void (*glCopyTexSubImage2D_fn)(GLenum, GLint, GLint, GLint, GLint, GLint, GLint, GLint);
typedef void (*glActiveTexture_fn)(GLenum);
typedef void (*glViewport_fn)(GLint, GLint, GLint, GLint);
typedef void (*glEnable_fn)(GLenum);
typedef void (*glDisable_fn)(GLenum);
typedef GLboolean (*glIsEnabled_fn)(GLenum);
typedef void (*glColorMask_fn)(GLboolean, GLboolean, GLboolean, GLboolean);
typedef void (*glGetBooleanv_fn)(GLenum, GLboolean *);
typedef void (*glGetIntegerv_fn)(GLenum, GLint *);
typedef void (*glBindBuffer_fn)(GLenum, GLuint);
typedef void (*glBindFramebuffer_fn)(GLenum, GLuint);
typedef void (*glEnableVertexAttribArray_fn)(GLuint);
typedef void (*glDisableVertexAttribArray_fn)(GLuint);
typedef void (*glVertexAttribPointer_fn)(GLuint, GLint, GLenum, GLboolean, GLint, const void *);
typedef void (*glGetVertexAttribiv_fn)(GLuint, GLenum, GLint *);
typedef void (*glGetVertexAttribPointerv_fn)(GLuint, GLenum, void **);
typedef void (*glDrawArrays_fn)(GLenum, GLint, GLint);
typedef void (*glBindVertexArray_fn)(GLuint);

static dlsym_fn real_dlsym;
static swap_fn real_swap;
static gpa_fn real_gpa;
static get_context_fn get_context;
static query_surface_fn query_surface;
static clock_gettime_fn real_clock_gettime;
static nanosleep_fn real_nanosleep;

static glCreateShader_fn gl_CreateShader;
static glShaderSource_fn gl_ShaderSource;
static glCompileShader_fn gl_CompileShader;
static glGetShaderiv_fn gl_GetShaderiv;
static glDeleteShader_fn gl_DeleteShader;
static glCreateProgram_fn gl_CreateProgram;
static glAttachShader_fn gl_AttachShader;
static glBindAttribLocation_fn gl_BindAttribLocation;
static glLinkProgram_fn gl_LinkProgram;
static glGetProgramiv_fn gl_GetProgramiv;
static glUseProgram_fn gl_UseProgram;
static glGetUniformLocation_fn gl_GetUniformLocation;
static glUniform1i_fn gl_Uniform1i;
static glUniform1f_fn gl_Uniform1f;
static glUniform2f_fn gl_Uniform2f;
static glGenTextures_fn gl_GenTextures;
static glDeleteTextures_fn gl_DeleteTextures;
static glBindTexture_fn gl_BindTexture;
static glTexParameteri_fn gl_TexParameteri;
static glTexImage2D_fn gl_TexImage2D;
static glCopyTexSubImage2D_fn gl_CopyTexSubImage2D;
static glActiveTexture_fn gl_ActiveTexture;
static glViewport_fn gl_Viewport;
static glEnable_fn gl_Enable;
static glDisable_fn gl_Disable;
static glIsEnabled_fn gl_IsEnabled;
static glColorMask_fn gl_ColorMask;
static glGetBooleanv_fn gl_GetBooleanv;
static glGetIntegerv_fn gl_GetIntegerv;
static glBindBuffer_fn gl_BindBuffer;
static glBindFramebuffer_fn gl_BindFramebuffer;
static glEnableVertexAttribArray_fn gl_EnableVertexAttribArray;
static glDisableVertexAttribArray_fn gl_DisableVertexAttribArray;
static glVertexAttribPointer_fn gl_VertexAttribPointer;
static glGetVertexAttribiv_fn gl_GetVertexAttribiv;
static glGetVertexAttribPointerv_fn gl_GetVertexAttribPointerv;
static glDrawArrays_fn gl_DrawArrays;
static glBindVertexArray_fn gl_BindVertexArray;

static void *libegl;
static void *libgles;
static void *libc_handle;
static int logged;
static volatile int resolving;

/* Estado do Scaler */
static GLuint prog_cas;
static GLuint prog_sharp;
static GLint u_cas_tex, u_cas_px, u_cas_sharp;
static GLint u_sharp_tex, u_sharp_px, u_sharp_sharp;
static GLuint scaler_tex;
static int scaler_tex_w, scaler_tex_h;
static int gl_initialized;
static double last_swap_sec;

static const float quad_verts[8] = {
    -1.0f, -1.0f,
     1.0f, -1.0f,
    -1.0f,  1.0f,
     1.0f,  1.0f
};

static const char *vs_src =
    "attribute vec2 aPos;\n"
    "varying vec2 vTexCoord;\n"
    "void main() {\n"
    "    vTexCoord = (aPos + 1.0) * 0.5;\n"
    "    gl_Position = vec4(aPos, 0.0, 1.0);\n"
    "}\n";

/* AMD Contrast Adaptive Sharpening (CAS) - versão GLES 2.0 otimizada para Mali Bifrost */
static const char *fs_cas_src =
    "precision mediump float;\n"
    "varying vec2 vTexCoord;\n"
    "uniform sampler2D uTex;\n"
    "uniform vec2 uPx;\n"
    "uniform float uSharp;\n"
    "void main() {\n"
    "    vec3 c = texture2D(uTex, vTexCoord).rgb;\n"
    "    vec3 t = texture2D(uTex, vTexCoord + vec2(0.0, -uPx.y)).rgb;\n"
    "    vec3 b = texture2D(uTex, vTexCoord + vec2(0.0,  uPx.y)).rgb;\n"
    "    vec3 l = texture2D(uTex, vTexCoord + vec2(-uPx.x, 0.0)).rgb;\n"
    "    vec3 r = texture2D(uTex, vTexCoord + vec2( uPx.x, 0.0)).rgb;\n"
    "    const vec3 lum = vec3(0.299, 0.587, 0.114);\n"
    "    float lc = dot(c, lum);\n"
    "    float lt = dot(t, lum);\n"
    "    float lb = dot(b, lum);\n"
    "    float ll = dot(l, lum);\n"
    "    float lr = dot(r, lum);\n"
    "    float min_l = min(lc, min(min(lt, lb), min(ll, lr)));\n"
    "    float max_l = max(lc, max(max(lt, lb), max(ll, lr)));\n"
    "    float amp = clamp(min(min_l, 1.0 - max_l) / max(max_l - min_l, 0.001), 0.0, 1.0);\n"
    "    float w = -sqrt(amp) * (uSharp * 0.20);\n"
    "    vec3 col = (c + (t + b + l + r) * w) / (1.0 + 4.0 * w);\n"
    "    gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);\n"
    "}\n";

/* Sharp Bilinear - preserva bordas nítidas sem ringing para ports 2D / pixel-art */
static const char *fs_sharp_src =
    "precision mediump float;\n"
    "varying vec2 vTexCoord;\n"
    "uniform sampler2D uTex;\n"
    "uniform vec2 uPx;\n"
    "uniform float uSharp;\n"
    "void main() {\n"
    "    vec2 res = 1.0 / uPx;\n"
    "    vec2 coord = vTexCoord * res - 0.5;\n"
    "    vec2 f = fract(coord);\n"
    "    float s = clamp(uSharp, 0.05, 1.0);\n"
    "    vec2 sharp_f = clamp((f - 0.5) / s + 0.5, 0.0, 1.0);\n"
    "    vec2 uv = (floor(coord) + 0.5 + sharp_f) * uPx;\n"
    "    gl_FragColor = texture2D(uTex, uv);\n"
    "}\n";

static void *rdlsym(void *h, const char *name)
{
    if (!real_dlsym) {
        static const char *versions[] = {"GLIBC_2.34", "GLIBC_2.17", "GLIBC_2.4", "GLIBC_2.2.5", 0};
        for (int i = 0; versions[i] && !real_dlsym; ++i)
            real_dlsym = (dlsym_fn)dlvsym(RTLD_NEXT, "dlsym", versions[i]);
    }
    return real_dlsym ? real_dlsym(h, name) : 0;
}

static void *egl_symbol(const char *name)
{
    if (!libegl) libegl = dlopen("libEGL.so.1", RTLD_LAZY);
    void *symbol = libegl ? rdlsym(libegl, name) : 0;
    return symbol ? symbol : rdlsym(RTLD_NEXT, name);
}

static void *gl_symbol(const char *name)
{
    if (!libgles) libgles = dlopen("libGLESv2.so.2", RTLD_LAZY);
    if (!libgles) libgles = dlopen("libGLESv2.so", RTLD_LAZY);
    void *symbol = libgles ? rdlsym(libgles, name) : 0;
    if (!symbol && real_gpa) symbol = real_gpa(name);
    return symbol ? symbol : rdlsym(RTLD_NEXT, name);
}

static void *libc_sym(const char *name)
{
    if (!libc_handle) libc_handle = dlopen("libc.so.6", RTLD_LAZY);
    void *sym = libc_handle ? rdlsym(libc_handle, name) : 0;
    return sym ? sym : rdlsym(RTLD_NEXT, name);
}

static int read_file_string(const char *path, char *buf, size_t max_len)
{
    int fd = open(path, O_RDONLY);
    if (fd < 0) return 0;
    ssize_t n = read(fd, buf, max_len - 1);
    close(fd);
    if (n <= 0) return 0;
    while (n > 0 && (buf[n - 1] == '\n' || buf[n - 1] == '\r' || buf[n - 1] == ' '))
        n--;
    buf[n] = '\0';
    return 1;
}

static float parse_float(const char *s, float dflt)
{
    if (!s || !*s) return dflt;
    float sign = 1.0f;
    if (*s == '-') { sign = -1.0f; s++; }
    float val = 0.0f;
    while (*s >= '0' && *s <= '9') {
        val = val * 10.0f + (*s - '0');
        s++;
    }
    if (*s == '.') {
        s++;
        float div = 10.0f;
        while (*s >= '0' && *s <= '9') {
            val += (*s - '0') / div;
            div *= 10.0f;
            s++;
        }
    }
    return sign * val;
}

static int parse_int(const char *s, int dflt)
{
    if (!s || !*s) return dflt;
    int sign = 1;
    if (*s == '-') { sign = -1; s++; }
    int val = 0;
    while (*s >= '0' && *s <= '9') {
        val = val * 10 + (*s - '0');
        s++;
    }
    return sign * val;
}

/* Modos: 0: off, 1: validate, 2: cas, 3: sharp, 4: pacing */
static int get_scaling_mode(void)
{
    char buf[32];
    const char *mode_str = 0;
    if (read_file_string("/dev/shm/omni36os-scaler-mode", buf, sizeof(buf))) {
        mode_str = buf;
    } else {
        const char *enabled = getenv("OMNI_SCALING");
        if (!enabled || (enabled[0] != '1' && strcmp(enabled, "true") != 0))
            return 0;
        mode_str = getenv("OMNI_SCALING_MODE");
    }
    if (!mode_str || !*mode_str || !strcmp(mode_str, "off") || !strcmp(mode_str, "0")) return 0;
    if (!strcmp(mode_str, "validate")) return 1;
    if (!strcmp(mode_str, "cas")) return 2;
    if (!strcmp(mode_str, "sharp")) return 3;
    if (!strcmp(mode_str, "pacing")) return 4;
    return 0;
}

static float get_sharpness(int mode)
{
    char buf[32];
    if (read_file_string("/dev/shm/omni36os-scaler-sharpness", buf, sizeof(buf)))
        return parse_float(buf, mode == 3 ? 0.25f : 0.6f);
    const char *env = getenv("OMNI_SCALING_SHARPNESS");
    if (env) return parse_float(env, mode == 3 ? 0.25f : 0.6f);
    return mode == 3 ? 0.25f : 0.6f;
}

static int is_pacing_active(int mode)
{
    if (mode == 4) return 1;
    char buf[16];
    if (read_file_string("/dev/shm/omni36os-scaler-pacing", buf, sizeof(buf)))
        return buf[0] == '1';
    const char *env = getenv("OMNI_SCALING_PACING");
    return env && (env[0] == '1' || !strcmp(env, "true"));
}

static int get_target_fps(void)
{
    char buf[16];
    if (read_file_string("/dev/shm/omni36os-fpscap", buf, sizeof(buf))) {
        int cap = parse_int(buf, 0);
        if (cap > 0) return cap;
    }
    if (read_file_string("/dev/shm/omni36os-scaler-target-fps", buf, sizeof(buf))) {
        int target = parse_int(buf, 60);
        if (target > 0) return target;
    }
    const char *env = getenv("OMNI_SCALING_TARGET_FPS");
    if (env) {
        int target = parse_int(env, 60);
        if (target > 0) return target;
    }
    return 60;
}

static double get_time_sec(void)
{
    if (!real_clock_gettime)
        real_clock_gettime = (clock_gettime_fn)libc_sym("clock_gettime");
    if (!real_clock_gettime) return 0.0;
    struct timespec ts;
    if (real_clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0.0;
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static void do_pacing(int target_fps)
{
    if (target_fps <= 0) target_fps = 60;
    if (!real_nanosleep)
        real_nanosleep = (nanosleep_fn)libc_sym("nanosleep");
    if (!real_nanosleep) return;

    double target_dt = 1.0 / (double)target_fps;
    double t_now = get_time_sec();
    if (last_swap_sec > 0.0) {
        double elapsed = t_now - last_swap_sec;
        if (elapsed < target_dt) {
            double sleep_s = target_dt - elapsed;
            if (sleep_s > 0.0003) {
                struct timespec req;
                req.tv_sec = (long)sleep_s;
                req.tv_nsec = (long)((sleep_s - (double)req.tv_sec) * 1e9);
                real_nanosleep(&req, 0);
            }
            t_now = get_time_sec();
        } else if (elapsed > target_dt * 1.5) {
            last_swap_sec = t_now;
            return;
        }
    }
    last_swap_sec = t_now;
}

static GLuint compile_shader(GLenum type, const char *src)
{
    GLuint s = gl_CreateShader(type);
    if (!s) return 0;
    gl_ShaderSource(s, 1, &src, 0);
    gl_CompileShader(s);
    GLint ok = 0;
    gl_GetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        gl_DeleteShader(s);
        return 0;
    }
    return s;
}

static GLuint create_program(const char *vs, const char *fs)
{
    GLuint v = compile_shader(GL_VERTEX_SHADER, vs);
    GLuint f = compile_shader(GL_FRAGMENT_SHADER, fs);
    if (!v || !f) {
        if (v) gl_DeleteShader(v);
        if (f) gl_DeleteShader(f);
        return 0;
    }
    GLuint p = gl_CreateProgram();
    if (!p) {
        gl_DeleteShader(v);
        gl_DeleteShader(f);
        return 0;
    }
    gl_AttachShader(p, v);
    gl_AttachShader(p, f);
    gl_BindAttribLocation(p, 0, "aPos");
    gl_LinkProgram(p);
    GLint ok = 0;
    gl_GetProgramiv(p, GL_LINK_STATUS, &ok);
    gl_DeleteShader(v);
    gl_DeleteShader(f);
    if (!ok) return 0;
    return p;
}

static int init_gl_scaler(void)
{
    if (gl_initialized) return 1;

#define L_GL(name) gl_##name = (gl##name##_fn)gl_symbol("gl" #name); if (!gl_##name) return 0
    L_GL(CreateShader);
    L_GL(ShaderSource);
    L_GL(CompileShader);
    L_GL(GetShaderiv);
    L_GL(DeleteShader);
    L_GL(CreateProgram);
    L_GL(AttachShader);
    L_GL(BindAttribLocation);
    L_GL(LinkProgram);
    L_GL(GetProgramiv);
    L_GL(UseProgram);
    L_GL(GetUniformLocation);
    L_GL(Uniform1i);
    L_GL(Uniform1f);
    L_GL(Uniform2f);
    L_GL(GenTextures);
    L_GL(DeleteTextures);
    L_GL(BindTexture);
    L_GL(TexParameteri);
    L_GL(TexImage2D);
    L_GL(CopyTexSubImage2D);
    L_GL(ActiveTexture);
    L_GL(Viewport);
    L_GL(Enable);
    L_GL(Disable);
    L_GL(IsEnabled);
    L_GL(ColorMask);
    L_GL(GetBooleanv);
    L_GL(GetIntegerv);
    L_GL(BindBuffer);
    L_GL(BindFramebuffer);
    L_GL(EnableVertexAttribArray);
    L_GL(DisableVertexAttribArray);
    L_GL(VertexAttribPointer);
    L_GL(GetVertexAttribiv);
    L_GL(GetVertexAttribPointerv);
    L_GL(DrawArrays);
#undef L_GL

    gl_BindVertexArray = (glBindVertexArray_fn)gl_symbol("glBindVertexArray");

    prog_cas = create_program(vs_src, fs_cas_src);
    if (prog_cas) {
        u_cas_tex = gl_GetUniformLocation(prog_cas, "uTex");
        u_cas_px = gl_GetUniformLocation(prog_cas, "uPx");
        u_cas_sharp = gl_GetUniformLocation(prog_cas, "uSharp");
    }

    prog_sharp = create_program(vs_src, fs_sharp_src);
    if (prog_sharp) {
        u_sharp_tex = gl_GetUniformLocation(prog_sharp, "uTex");
        u_sharp_px = gl_GetUniformLocation(prog_sharp, "uPx");
        u_sharp_sharp = gl_GetUniformLocation(prog_sharp, "uSharp");
    }

    gl_initialized = 1;
    return (prog_cas || prog_sharp);
}

static void log_state(int mode, int width, int height, float sharpness, int pacing)
{
    if (logged) return;
    char message[256];
    size_t n = 0;
    const char *prefix = "omni_scaler: ";
    for (size_t i = 0; prefix[i]; ++i) message[n++] = prefix[i];

    const char *mode_names[] = {"disabled", "validate", "cas", "sharp", "pacing"};
    const char *mname = (mode >= 0 && mode <= 4) ? mode_names[mode] : "unknown";
    const char *str_mode = "mode=";
    for (size_t i = 0; str_mode[i]; ++i) message[n++] = str_mode[i];
    for (size_t i = 0; mname[i]; ++i) message[n++] = mname[i];

    const char *str_surf = ", surface=";
    for (size_t i = 0; str_surf[i]; ++i) message[n++] = str_surf[i];
    int values[2] = {width, height};
    for (int v = 0; v < 2; ++v) {
        int val = values[v], digits[10], count = 0;
        do { digits[count++] = val % 10; val /= 10; } while (val && count < 10);
        while (count) message[n++] = (char)('0' + digits[--count]);
        if (v == 0) message[n++] = 'x';
    }

    if (mode == 2 || mode == 3) {
        const char *str_sharp = ", sharp=";
        for (size_t i = 0; str_sharp[i]; ++i) message[n++] = str_sharp[i];
        int s_int = (int)sharpness;
        int s_frac = (int)((sharpness - (float)s_int) * 100.0f);
        if (s_frac < 0) s_frac = 0;
        message[n++] = (char)('0' + s_int);
        message[n++] = '.';
        message[n++] = (char)('0' + (s_frac / 10));
        message[n++] = (char)('0' + (s_frac % 10));
    }

    const char *str_pace = pacing ? ", pacing=on\n" : ", pacing=off\n";
    for (size_t i = 0; str_pace[i]; ++i) message[n++] = str_pace[i];

    int fd = open("/dev/shm/omni36os-scaler.log", O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0600);
    if (fd >= 0) {
        write(fd, message, n);
        close(fd);
    }
    logged = 1;
}

static void apply_spatial_filter(int mode, int width, int height, float sharpness)
{
    GLuint active_prog = (mode == 2) ? prog_cas : prog_sharp;
    if (!active_prog) return;

    /* Salva estado GL */
    GLint prev_prog = 0, prev_active_tex = 0, prev_tex2d = 0;
    GLint prev_buf = 0, prev_fb = 0, prev_vao = 0;
    GLint prev_vp[4];
    GLboolean prev_blend, prev_depth, prev_scissor, prev_cull, prev_stencil;
    GLboolean prev_colormask[4];
    GLint prev_attr_en = 0, prev_attr_sz = 0, prev_attr_ty = 0, prev_attr_norm = 0, prev_attr_stride = 0, prev_attr_buf = 0;
    void *prev_attr_ptr = 0;

    gl_GetIntegerv(GL_CURRENT_PROGRAM, &prev_prog);
    gl_GetIntegerv(GL_ACTIVE_TEXTURE, &prev_active_tex);
    gl_GetIntegerv(GL_TEXTURE_BINDING_2D, &prev_tex2d);
    gl_GetIntegerv(GL_ARRAY_BUFFER_BINDING, &prev_buf);
    gl_GetIntegerv(GL_FRAMEBUFFER_BINDING, &prev_fb);
    gl_GetIntegerv(GL_VIEWPORT, prev_vp);

    prev_blend = gl_IsEnabled(GL_BLEND);
    prev_depth = gl_IsEnabled(GL_DEPTH_TEST);
    prev_scissor = gl_IsEnabled(GL_SCISSOR_TEST);
    prev_cull = gl_IsEnabled(GL_CULL_FACE);
    prev_stencil = gl_IsEnabled(GL_STENCIL_TEST);
    gl_GetBooleanv(GL_COLOR_WRITEMASK, prev_colormask);

    if (gl_BindVertexArray) {
        gl_GetIntegerv(GL_VERTEX_ARRAY_BINDING, &prev_vao);
        if (prev_vao) gl_BindVertexArray(0);
    }

    gl_GetVertexAttribiv(0, GL_VERTEX_ATTRIB_ARRAY_ENABLED, &prev_attr_en);
    gl_GetVertexAttribiv(0, GL_VERTEX_ATTRIB_ARRAY_SIZE, &prev_attr_sz);
    gl_GetVertexAttribiv(0, GL_VERTEX_ATTRIB_ARRAY_TYPE, &prev_attr_ty);
    gl_GetVertexAttribiv(0, GL_VERTEX_ATTRIB_ARRAY_NORMALIZED, &prev_attr_norm);
    gl_GetVertexAttribiv(0, GL_VERTEX_ATTRIB_ARRAY_STRIDE, &prev_attr_stride);
    gl_GetVertexAttribiv(0, GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING, &prev_attr_buf);
    gl_GetVertexAttribPointerv(0, GL_VERTEX_ATTRIB_ARRAY_POINTER, &prev_attr_ptr);

    /* Garante textura auxiliar */
    gl_ActiveTexture(GL_TEXTURE0);
    if (!scaler_tex) {
        gl_GenTextures(1, &scaler_tex);
        gl_BindTexture(GL_TEXTURE_2D, scaler_tex);
        gl_TexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        gl_TexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        gl_TexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        gl_TexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        gl_TexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, 0);
        scaler_tex_w = width;
        scaler_tex_h = height;
    } else {
        gl_BindTexture(GL_TEXTURE_2D, scaler_tex);
        if (scaler_tex_w != width || scaler_tex_h != height) {
            gl_TexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, 0);
            scaler_tex_w = width;
            scaler_tex_h = height;
        }
    }

    /* Copia o frame renderizado do default framebuffer para a textura */
    gl_CopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, width, height);

    /* Configura render pass */
    gl_BindFramebuffer(GL_FRAMEBUFFER, 0);
    gl_Viewport(0, 0, width, height);
    gl_Disable(GL_BLEND);
    gl_Disable(GL_DEPTH_TEST);
    gl_Disable(GL_SCISSOR_TEST);
    gl_Disable(GL_CULL_FACE);
    gl_Disable(GL_STENCIL_TEST);
    gl_ColorMask(1, 1, 1, 1);

    gl_UseProgram(active_prog);
    gl_BindBuffer(GL_ARRAY_BUFFER, 0);

    if (mode == 2) {
        gl_Uniform1i(u_cas_tex, 0);
        gl_Uniform2f(u_cas_px, 1.0f / (float)width, 1.0f / (float)height);
        gl_Uniform1f(u_cas_sharp, sharpness);
    } else {
        gl_Uniform1i(u_sharp_tex, 0);
        gl_Uniform2f(u_sharp_px, 1.0f / (float)width, 1.0f / (float)height);
        gl_Uniform1f(u_sharp_sharp, sharpness);
    }

    gl_EnableVertexAttribArray(0);
    gl_VertexAttribPointer(0, 2, GL_FLOAT, 0, 0, quad_verts);
    gl_DrawArrays(GL_TRIANGLE_STRIP, 0, 4);

    /* Restaura estado GL */
    gl_BindBuffer(GL_ARRAY_BUFFER, prev_attr_buf);
    gl_VertexAttribPointer(0, prev_attr_sz, prev_attr_ty, prev_attr_norm, prev_attr_stride, prev_attr_ptr);
    if (!prev_attr_en) gl_DisableVertexAttribArray(0);

    if (gl_BindVertexArray && prev_vao)
        gl_BindVertexArray(prev_vao);

    gl_ColorMask(prev_colormask[0], prev_colormask[1], prev_colormask[2], prev_colormask[3]);
    if (prev_blend) gl_Enable(GL_BLEND);
    if (prev_depth) gl_Enable(GL_DEPTH_TEST);
    if (prev_scissor) gl_Enable(GL_SCISSOR_TEST);
    if (prev_cull) gl_Enable(GL_CULL_FACE);
    if (prev_stencil) gl_Enable(GL_STENCIL_TEST);

    gl_BindFramebuffer(GL_FRAMEBUFFER, prev_fb);
    gl_Viewport(prev_vp[0], prev_vp[1], prev_vp[2], prev_vp[3]);
    gl_UseProgram(prev_prog);
    gl_ActiveTexture(prev_active_tex);
    gl_BindTexture(GL_TEXTURE_2D, prev_tex2d);
    gl_BindBuffer(GL_ARRAY_BUFFER, prev_buf);
}

unsigned eglSwapBuffers(void *display, void *surface)
{
    swap_fn next = real_swap;
    if (!next && !resolving) {
        resolving = 1;
        next = (swap_fn)rdlsym(RTLD_NEXT, "eglSwapBuffers");
        if (!next) next = (swap_fn)egl_symbol("eglSwapBuffers");
        if (next == eglSwapBuffers) next = 0;
        real_swap = next;
        resolving = 0;
    }
    if (!next) return 0;

    int mode = get_scaling_mode();
    if (mode == 0) return next(display, surface);

    if (!get_context) get_context = (get_context_fn)egl_symbol("eglGetCurrentContext");
    if (!query_surface) query_surface = (query_surface_fn)egl_symbol("eglQuerySurface");

    int width = 0, height = 0;
    if (query_surface && get_context && get_context()) {
        query_surface(display, surface, 0x3057, &width);
        query_surface(display, surface, 0x3056, &height);
    }

    float sharpness = get_sharpness(mode);
    int pacing = is_pacing_active(mode);

    if (width > 0 && height > 0) {
        log_state(mode, width, height, sharpness, pacing);
        if (mode == 2 || mode == 3) {
            if (init_gl_scaler())
                apply_spatial_filter(mode, width, height, sharpness);
        }
    }

    if (pacing)
        do_pacing(get_target_fps());

    return next(display, surface);
}

void *eglGetProcAddress(const char *name)
{
    if (!real_gpa) real_gpa = (gpa_fn)rdlsym(RTLD_NEXT, "eglGetProcAddress");
    if (name && !strcmp(name, "eglSwapBuffers")) {
        if (real_gpa && !real_swap) real_swap = (swap_fn)real_gpa(name);
        return (void *)eglSwapBuffers;
    }
    return real_gpa ? real_gpa(name) : 0;
}

void *dlsym(void *handle, const char *name)
{
    void *symbol = rdlsym(handle, name);
    if (!symbol || !name) return symbol;
    if (!strcmp(name, "eglSwapBuffers")) {
        if (!real_swap) real_swap = (swap_fn)symbol;
        return (void *)eglSwapBuffers;
    }
    if (!strcmp(name, "eglGetProcAddress")) {
        if (!real_gpa) real_gpa = (gpa_fn)symbol;
        return (void *)eglGetProcAddress;
    }
    return symbol;
}
