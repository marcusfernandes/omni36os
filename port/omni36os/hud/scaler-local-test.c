#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#ifndef EGL_PLATFORM_SURFACELESS_MESA
#define EGL_PLATFORM_SURFACELESS_MESA 0x31DD
#endif

static const char *vs = "attribute vec2 p; void main(){gl_Position=vec4(p,0,1);}";
static const char *fs = "precision mediump float; uniform vec4 c; void main(){gl_FragColor=c;}";
static GLuint make_shader(GLenum type, const char *src) {
    GLuint s=glCreateShader(type); GLint ok=0; glShaderSource(s,1,&src,0); glCompileShader(s); glGetShaderiv(s,GL_COMPILE_STATUS,&ok); return ok?s:0;
}
int main(void) {
    EGLDisplay d=eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (d==EGL_NO_DISPLAY || !eglInitialize(d,0,0)) {
        PFNEGLGETPLATFORMDISPLAYPROC get_platform = (PFNEGLGETPLATFORMDISPLAYPROC)eglGetProcAddress("eglGetPlatformDisplay");
        if (!get_platform) get_platform = (PFNEGLGETPLATFORMDISPLAYPROC)eglGetProcAddress("eglGetPlatformDisplayEXT");
        d = get_platform ? get_platform(EGL_PLATFORM_SURFACELESS_MESA, EGL_DEFAULT_DISPLAY, 0) : EGL_NO_DISPLAY;
        if (d == EGL_NO_DISPLAY || !eglInitialize(d,0,0)) { fprintf(stderr,"EGL init failed\n"); return 1; }
    }
    EGLint attrs[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES2_BIT,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_NONE};
    EGLConfig cfg; EGLint n=0; if(!eglChooseConfig(d,attrs,&cfg,1,&n)||!n) return 2;
    EGLint pa[]={EGL_WIDTH,320,EGL_HEIGHT,240,EGL_NONE}; EGLSurface s=eglCreatePbufferSurface(d,cfg,pa);
    EGLint ca[]={EGL_CONTEXT_CLIENT_VERSION,2,EGL_NONE}; EGLContext c=eglCreateContext(d,cfg,EGL_NO_CONTEXT,ca);
    if(s==EGL_NO_SURFACE||c==EGL_NO_CONTEXT||!eglMakeCurrent(d,s,s,c)) return 3;
    GLuint p=glCreateProgram(), a=make_shader(GL_VERTEX_SHADER,vs), b=make_shader(GL_FRAGMENT_SHADER,fs); glAttachShader(p,a); glAttachShader(p,b); glBindAttribLocation(p,0,"p"); glLinkProgram(p); glUseProgram(p);
    GLint color=glGetUniformLocation(p,"c"); GLfloat verts[]={-1,-1,1,-1,-1,1,1,1}; glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,0,verts); glEnableVertexAttribArray(0);
    for(int i=0;i<240;i++) { float x=(float)(i%120)/120.0f; glViewport(0,0,320,240); glClearColor(x,0.15f,1.0f-x,1); glClear(GL_COLOR_BUFFER_BIT); glUniform4f(color,1-x,x,0.4f,1); glDrawArrays(GL_TRIANGLE_STRIP,0,4); if(!eglSwapBuffers(d,s)){fprintf(stderr,"swap failed\n");break;} usleep(16000); }
    typedef EGLBoolean (*swap_fn)(EGLDisplay, EGLSurface);
    swap_fn swap_proc=(swap_fn)eglGetProcAddress("eglSwapBuffers");
    swap_fn swap_sym=(swap_fn)dlsym(RTLD_DEFAULT,"eglSwapBuffers");
    if(!swap_proc || !swap_sym || swap_proc!=swap_sym){fprintf(stderr,"swap symbol interception failed\n");return 4;}
    glFinish(); eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT); eglDestroySurface(d,s); eglDestroyContext(d,c); eglTerminate(d); return 0;
}
