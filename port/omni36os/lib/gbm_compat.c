/* Omni36OS — funções do libgbm novo que o libgbm do Mali (dArkOSen) não tem.
 * O WPE WebKit (navegador Cog) pede estas; aqui elas viram as equivalentes de plano único.
 * Entra por LD_PRELOAD só no navegador. Sem headers: o cross-compilador não tem sysroot.
 *   aarch64-linux-gnu-gcc -O2 -fPIC -shared -nostdlib -o gbm_compat.so gbm_compat.c */
typedef unsigned int u32;
typedef unsigned long long u64;
struct gbm_bo;
struct gbm_device;
union gbm_bo_handle { void *ptr; int s32; u32 u32; long long s64; u64 u64; };

extern union gbm_bo_handle gbm_bo_get_handle(struct gbm_bo *bo);
extern u32 gbm_bo_get_stride(struct gbm_bo *bo);
extern int gbm_bo_get_fd(struct gbm_bo *bo);
extern struct gbm_bo *gbm_bo_create(struct gbm_device *d, u32 w, u32 h, u32 format, u32 flags);

#define DRM_FORMAT_MOD_INVALID 0x00ffffffffffffffULL

int gbm_bo_get_plane_count(struct gbm_bo *bo) { (void)bo; return 1; }
union gbm_bo_handle gbm_bo_get_handle_for_plane(struct gbm_bo *bo, int plane)
{
    if (plane == 0)
        return gbm_bo_get_handle(bo);
    union gbm_bo_handle h; h.u64 = 0; return h;
}
u32 gbm_bo_get_stride_for_plane(struct gbm_bo *bo, int plane) { return plane == 0 ? gbm_bo_get_stride(bo) : 0; }
u32 gbm_bo_get_offset(struct gbm_bo *bo, int plane) { (void)bo; (void)plane; return 0; }
u64 gbm_bo_get_modifier(struct gbm_bo *bo) { (void)bo; return DRM_FORMAT_MOD_INVALID; }
int gbm_bo_get_fd_for_plane(struct gbm_bo *bo, int plane) { return plane == 0 ? gbm_bo_get_fd(bo) : -1; }
struct gbm_bo *gbm_bo_create_with_modifiers2(struct gbm_device *d, u32 w, u32 h, u32 format,
                                             const u64 *mods, const unsigned count, u32 flags)
{
    (void)mods; (void)count;
    return gbm_bo_create(d, w, h, format, flags);
}
/* mapear para a CPU: o Mali não oferece; quem pede cai no caminho de cópia */
void *gbm_bo_map(struct gbm_bo *bo, u32 x, u32 y, u32 w, u32 h, u32 flags, u32 *stride, void **data)
{
    (void)bo; (void)x; (void)y; (void)w; (void)h; (void)flags; (void)stride;
    if (data) *data = 0;
    return 0;
}
void gbm_bo_unmap(struct gbm_bo *bo, void *data) { (void)bo; (void)data; }
