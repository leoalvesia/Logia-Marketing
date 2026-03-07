import { useState, useRef, useCallback } from "react";
import { useSettingsStore } from "@/stores/settingsStore";
import { Upload, X } from "lucide-react";

const GOOGLE_FONTS = [
    "Inter", "Roboto", "Poppins", "Montserrat", "DM Sans",
    "Nunito", "Lato", "Source Sans 3", "Raleway", "Work Sans",
];

const CHANNEL_COLORS = {
    primary: { label: "Cor primária", hint: "Botões, destaques" },
    secondary: { label: "Cor secundária", hint: "Acentos, badges" },
};

// ── Color swatch picker ───────────────────────────────────────────────────────
function ColorField({ id, label, hint, value, onChange }) {
    return (
        <div className="space-y-1.5">
            <label htmlFor={id} className="text-xs font-medium text-[#9CA3AF]">
                {label} <span className="text-[#4B5563]">— {hint}</span>
            </label>
            <div className="flex items-center gap-3">
                <div className="relative">
                    <input
                        id={id}
                        type="color"
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        className="w-10 h-10 rounded-lg border border-[#2E2E2E] bg-[#1A1A1A] cursor-pointer
                       focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                        aria-label={label}
                    />
                </div>
                <div className="flex-1">
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => /^#[0-9A-Fa-f]{0,6}$/.test(e.target.value) && onChange(e.target.value)}
                        maxLength={7}
                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-xs font-mono text-[#F9FAFB]
                       focus:outline-none focus:border-[#6366F1] focus:ring-2 focus:ring-[#6366F1]/30 transition-colors"
                        aria-label={`Código hexadecimal de ${label}`}
                    />
                </div>
                {/* Live preview swatch */}
                <div
                    className="w-8 h-8 rounded-lg border border-[#2E2E2E] shadow-inner"
                    style={{ background: value }}
                    aria-hidden="true"
                    title={value}
                />
            </div>
        </div>
    );
}

// ── Logo drop zone ─────────────────────────────────────────────────────────────
function LogoDropZone({ logoDataUrl, onChange }) {
    const inputRef = useRef();
    const [dragOver, setDragOver] = useState(false);

    const handleFiles = useCallback((files) => {
        const file = files?.[0];
        if (!file || !file.type.startsWith("image/")) return;
        const reader = new FileReader();
        reader.onload = (e) => onChange(e.target.result);
        reader.readAsDataURL(file);
    }, [onChange]);

    return (
        <div className="space-y-1.5">
            <p className="text-xs font-medium text-[#9CA3AF]">Logo da Marca</p>
            <div
                role="region"
                aria-label="Área de upload do logo"
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
                className={[
                    "relative border-2 border-dashed rounded-xl transition-all",
                    dragOver ? "border-[#6366F1] bg-[#6366F1]/5" : "border-[#2E2E2E] bg-[#1A1A1A]",
                ].join(" ")}
            >
                {logoDataUrl ? (
                    <div className="flex items-center gap-4 p-4">
                        <img
                            src={logoDataUrl}
                            alt="Logo pré-visualização"
                            className="w-24 h-24 object-contain rounded-lg bg-[#0F0F0F] border border-[#2E2E2E]"
                        />
                        <div className="space-y-2">
                            <p className="text-xs text-[#9CA3AF]">Logo carregada</p>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => inputRef.current?.click()}
                                    className="text-xs text-[#6366F1] hover:text-[#818CF8] transition-colors focus-visible:outline-2 focus-visible:outline-[#6366F1] rounded"
                                >
                                    Trocar
                                </button>
                                <button
                                    onClick={() => onChange(null)}
                                    aria-label="Remover logo"
                                    className="text-xs text-red-400 hover:text-red-300 transition-colors focus-visible:outline-2 focus-visible:outline-[#6366F1] rounded"
                                >
                                    <X size={12} className="inline" aria-hidden="true" /> Remover
                                </button>
                            </div>
                        </div>
                    </div>
                ) : (
                    <button
                        onClick={() => inputRef.current?.click()}
                        aria-label="Clique ou arraste para enviar logo"
                        className="w-full flex flex-col items-center gap-2 p-8 text-[#6B7280] hover:text-[#9CA3AF] transition-colors focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                    >
                        <Upload size={28} aria-hidden="true" />
                        <span className="text-xs">Arraste ou clique para enviar</span>
                        <span className="text-[10px] text-[#4B5563]">PNG, SVG, JPG · máx 2MB</span>
                    </button>
                )}
                <input
                    ref={inputRef}
                    type="file"
                    accept="image/*"
                    className="sr-only"
                    aria-hidden="true"
                    onChange={(e) => handleFiles(e.target.files)}
                />
            </div>
        </div>
    );
}

// ── Post preview ──────────────────────────────────────────────────────────────
function PostPreview({ brand }) {
    return (
        <div className="space-y-2" aria-label="Pré-visualização do design dos posts">
            <p className="text-xs font-medium text-[#9CA3AF]">Pré-visualização</p>
            <div
                className="rounded-xl border border-[#2E2E2E] overflow-hidden"
                role="img"
                aria-label="Preview de como ficará o design dos posts com as configurações atuais"
            >
                {/* Header bar */}
                <div className="flex items-center gap-2 px-4 py-2.5" style={{ background: brand.primaryColor }}>
                    {brand.logoDataUrl ? (
                        <img src={brand.logoDataUrl} alt="Logo" className="w-6 h-6 object-contain rounded" />
                    ) : (
                        <div className="w-6 h-6 rounded bg-white/20 flex items-center justify-center text-white font-bold text-xs">L</div>
                    )}
                    <span className="text-white text-xs font-semibold" style={{ fontFamily: brand.fontFamily }}>
                        Logia Marketing
                    </span>
                </div>

                {/* Body */}
                <div className="bg-[#0F0F0F] p-4 space-y-3">
                    <p className="text-sm text-[#F9FAFB] leading-relaxed" style={{ fontFamily: brand.fontFamily }}>
                        ✨ A IA generativa está transformando como PMEs fazem marketing. Clique para saber mais.
                    </p>
                    <div className="flex gap-2">
                        <span
                            className="text-[10px] font-semibold px-3 py-1 rounded-full text-white"
                            style={{ background: brand.primaryColor }}
                        >
                            Saiba mais
                        </span>
                        <span
                            className="text-[10px] font-semibold px-3 py-1 rounded-full text-white"
                            style={{ background: brand.secondaryColor }}
                        >
                            #IA #PME
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function BrandIdentityTab({ onSave }) {
    const brand = useSettingsStore((s) => s.brand);
    const updateBrand = useSettingsStore((s) => s.updateBrand);

    return (
        <section aria-label="Identidade visual da marca" className="space-y-6">
            {/* Colors */}
            <div className="space-y-4">
                <h3 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Cores da Marca</h3>
                <div className="grid sm:grid-cols-2 gap-4">
                    <ColorField
                        id="brand-primary"
                        label="Cor primária"
                        hint="Botões, destaques"
                        value={brand.primaryColor}
                        onChange={(v) => updateBrand({ primaryColor: v })}
                    />
                    <ColorField
                        id="brand-secondary"
                        label="Cor secundária"
                        hint="Acentos, badges"
                        value={brand.secondaryColor}
                        onChange={(v) => updateBrand({ secondaryColor: v })}
                    />
                </div>
            </div>

            {/* Logo */}
            <div>
                <h3 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-3">Logo</h3>
                <LogoDropZone
                    logoDataUrl={brand.logoDataUrl}
                    onChange={(v) => updateBrand({ logoDataUrl: v })}
                />
            </div>

            {/* Font */}
            <div className="space-y-1.5">
                <h3 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Tipografia</h3>
                <div className="space-y-1.5">
                    <label htmlFor="font-select" className="text-xs text-[#9CA3AF]">Fonte dos posts</label>
                    <select
                        id="font-select"
                        value={brand.fontFamily}
                        onChange={(e) => updateBrand({ fontFamily: e.target.value })}
                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] focus:outline-none focus:border-[#6366F1] focus:ring-2 focus:ring-[#6366F1]/30 [color-scheme:dark]"
                        style={{ fontFamily: brand.fontFamily }}
                    >
                        {GOOGLE_FONTS.map((f) => (
                            <option key={f} value={f} style={{ fontFamily: f }}>{f}</option>
                        ))}
                    </select>
                    <p className="text-[10px] text-[#4B5563]">Fonte aplicada em copy e cabeçalhos dos posts gerados.</p>
                </div>
            </div>

            {/* Live preview */}
            <PostPreview brand={brand} />

            {/* Save */}
            <div className="flex justify-end">
                <button
                    onClick={onSave}
                    className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-sm font-semibold px-6 py-2.5 rounded-lg transition-all focus-visible:outline-2 focus-visible:outline-[#6366F1] shadow-[0_0_14px_rgba(99,102,241,0.3)]"
                >
                    Salvar Identidade
                </button>
            </div>
        </section>
    );
}
