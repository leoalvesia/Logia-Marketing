/**
 * Política de Privacidade — Logia Marketing Platform
 * Rota pública: /privacy
 * Elaborada em conformidade com a LGPD (Lei nº 13.709/2018)
 */
import { Link } from "react-router-dom";
import { ArrowLeft, Shield } from "lucide-react";

const LAST_UPDATED = "7 de março de 2026";
const DPO_EMAIL = "privacidade@logia.com.br";

export default function PrivacyPage() {
    return (
        <main className="min-h-screen bg-[#0F0F0F] text-[#F9FAFB] px-4 py-10">
            <div className="max-w-2xl mx-auto space-y-8">
                {/* Header */}
                <div className="space-y-3">
                    <Link
                        to="/"
                        className="inline-flex items-center gap-2 text-sm text-[#9CA3AF] hover:text-[#F9FAFB] transition-colors"
                    >
                        <ArrowLeft size={14} aria-hidden="true" />
                        Voltar
                    </Link>
                    <div className="flex items-center gap-3">
                        <Shield size={20} className="text-[#6366F1]" aria-hidden="true" />
                        <h1 className="text-2xl font-bold text-[#F9FAFB]">Política de Privacidade</h1>
                    </div>
                    <p className="text-sm text-[#6B7280]">
                        Última atualização: {LAST_UPDATED} · Conformidade LGPD (Lei nº 13.709/2018)
                    </p>
                </div>

                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4 text-sm text-[#9CA3AF]">
                    <strong className="text-[#F9FAFB]">Resumo simples:</strong> Coletamos apenas
                    os dados necessários para o serviço funcionar. Nunca vendemos seus dados.
                    Você pode exportar ou excluir sua conta a qualquer momento.
                </div>

                <Section title="1. Controlador dos Dados">
                    <p>
                        O controlador dos seus dados pessoais é a <strong>Logia Tecnologia Ltda.</strong>
                        , com sede em São Paulo/SP. Nosso Encarregado de Proteção de Dados (DPO)
                        pode ser contactado em{" "}
                        <a href={`mailto:${DPO_EMAIL}`} className="text-[#6366F1] hover:underline">
                            {DPO_EMAIL}
                        </a>.
                    </p>
                </Section>

                <Section title="2. Dados Coletados e Finalidades">
                    <table className="w-full text-xs border-collapse">
                        <thead>
                            <tr className="border-b border-[#2E2E2E]">
                                <th className="text-left py-2 text-[#F9FAFB] font-medium">Dado</th>
                                <th className="text-left py-2 text-[#F9FAFB] font-medium">Finalidade</th>
                                <th className="text-left py-2 text-[#F9FAFB] font-medium">Base legal</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#2E2E2E]">
                            {[
                                ["Nome e email", "Autenticação e comunicação", "Execução de contrato"],
                                ["Nicho e persona", "Geração de conteúdo personalizado", "Execução de contrato"],
                                ["Tokens de redes sociais", "Publicação automática autorizada por você", "Consentimento explícito"],
                                ["Conteúdo gerado (copies, artes)", "Histórico e reaproveitamento", "Execução de contrato"],
                                ["Logs de acesso", "Segurança e debugging", "Interesse legítimo"],
                                ["NPS e feedbacks", "Melhoria do produto", "Consentimento"],
                                ["Dados de uso (IP, user-agent)", "Rate limiting e segurança", "Interesse legítimo"],
                            ].map(([dado, fin, base]) => (
                                <tr key={dado}>
                                    <td className="py-2 pr-3 text-[#F9FAFB]">{dado}</td>
                                    <td className="py-2 pr-3">{fin}</td>
                                    <td className="py-2 text-[#6B7280]">{base}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </Section>

                <Section title="3. Compartilhamento de Dados">
                    <p>Seus dados são compartilhados <strong>exclusivamente</strong> com:</p>
                    <ul>
                        <li><strong>Anthropic / OpenAI</strong> — para geração de conteúdo IA (texto enviado como prompt)</li>
                        <li><strong>Meta / Instagram</strong> — para publicação quando você autoriza</li>
                        <li><strong>Google Drive</strong> — para armazenamento de artes quando você conecta</li>
                        <li><strong>Sentry</strong> — para monitoramento de erros (sem dados pessoais)</li>
                        <li><strong>Resend</strong> — para envio de emails transacionais</li>
                    </ul>
                    <p className="mt-2 text-[#6B7280]">
                        Nunca vendemos, alugamos ou compartilhamos seus dados para fins de publicidade
                        ou com terceiros não listados acima.
                    </p>
                </Section>

                <Section title="4. Retenção dos Dados">
                    <ul>
                        <li><strong>Conta ativa:</strong> dados mantidos enquanto a conta existir</li>
                        <li><strong>Após exclusão:</strong> anonimização imediata + exclusão definitiva em 30 dias</li>
                        <li><strong>Logs de segurança:</strong> retidos por 90 dias</li>
                        <li><strong>Backups:</strong> sobrescritos após 30 dias</li>
                    </ul>
                </Section>

                <Section title="5. Segurança">
                    <ul>
                        <li>Senhas armazenadas com bcrypt (fator 12)</li>
                        <li>Tokens OAuth criptografados com AES-128 (Fernet)</li>
                        <li>Comunicação exclusivamente via HTTPS (TLS 1.2+)</li>
                        <li>Banco de dados e Redis não expostos à internet pública</li>
                        <li>Monitoramento de segurança 24/7 via Sentry</li>
                    </ul>
                </Section>

                <Section title="6. Seus Direitos (LGPD Art. 18)">
                    <p>Você tem direito a:</p>
                    <ul>
                        <li>
                            <strong>Acesso e portabilidade:</strong>{" "}
                            <Link to="/settings" className="text-[#6366F1] hover:underline">
                                Configurações → Exportar meus dados
                            </Link>
                        </li>
                        <li>
                            <strong>Correção:</strong> editar seus dados em Configurações a qualquer momento
                        </li>
                        <li>
                            <strong>Exclusão:</strong>{" "}
                            <Link to="/settings" className="text-[#6366F1] hover:underline">
                                Configurações → Excluir conta
                            </Link>{" "}
                            — anonimização imediata, exclusão em 30 dias
                        </li>
                        <li>
                            <strong>Revogação de consentimento:</strong> desconectar redes sociais em Configurações
                        </li>
                        <li>
                            <strong>Reclamação:</strong> junto à ANPD (Autoridade Nacional de Proteção de Dados)
                            em <a href="https://www.gov.br/anpd" className="text-[#6366F1] hover:underline" target="_blank" rel="noopener noreferrer">gov.br/anpd</a>
                        </li>
                    </ul>
                </Section>

                <Section title="7. Cookies">
                    <p>
                        A Logia utiliza apenas cookies de sessão necessários para autenticação
                        (localStorage) e preferências (localStorage). Não usamos cookies de
                        rastreamento ou publicidade.
                    </p>
                </Section>

                <Section title="8. Contato">
                    <p>
                        Para exercer seus direitos ou tirar dúvidas sobre privacidade, entre em
                        contato com nosso DPO:{" "}
                        <a href={`mailto:${DPO_EMAIL}`} className="text-[#6366F1] hover:underline">
                            {DPO_EMAIL}
                        </a>
                    </p>
                    <p className="text-[#6B7280]">
                        Respondemos em até 15 dias úteis, conforme exigido pela LGPD.
                    </p>
                </Section>

                <div className="border-t border-[#2E2E2E] pt-6 flex flex-wrap gap-4 text-sm text-[#6B7280]">
                    <Link to="/terms" className="hover:text-[#9CA3AF] transition-colors">
                        Termos de Uso
                    </Link>
                    <a href={`mailto:${DPO_EMAIL}`} className="hover:text-[#9CA3AF] transition-colors">
                        Contato DPO
                    </a>
                </div>
            </div>
        </main>
    );
}

function Section({ title, children }) {
    return (
        <section className="space-y-3">
            <h2 className="text-base font-semibold text-[#F9FAFB]">{title}</h2>
            <div className="text-sm text-[#9CA3AF] leading-relaxed space-y-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1">
                {children}
            </div>
        </section>
    );
}
