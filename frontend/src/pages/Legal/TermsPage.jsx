/**
 * Termos de Uso — Logia Marketing Platform
 * Rota pública: /terms
 */
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

const LAST_UPDATED = "7 de março de 2026";
const COMPANY = "Logia Tecnologia Ltda.";
const EMAIL = "juridico@logia.com.br";

export default function TermsPage() {
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
                    <h1 className="text-2xl font-bold text-[#F9FAFB]">Termos de Uso</h1>
                    <p className="text-sm text-[#6B7280]">Última atualização: {LAST_UPDATED}</p>
                </div>

                <Section title="1. Aceitação dos Termos">
                    <p>
                        Ao criar uma conta e utilizar a plataforma Logia, você concorda com estes
                        Termos de Uso. Se não concordar com qualquer disposição, não utilize o
                        serviço.
                    </p>
                </Section>

                <Section title="2. Descrição do Serviço">
                    <p>
                        A Logia é uma plataforma de criação e distribuição de conteúdo com inteligência
                        artificial para consultores e pequenas empresas brasileiras. O serviço inclui
                        geração de copy, criação de arte, agendamento de publicações e análise de
                        tendências de mercado.
                    </p>
                </Section>

                <Section title="3. Cadastro e Acesso">
                    <ul>
                        <li>O acesso ao beta é controlado por convites — você precisa de um código válido para se registrar.</li>
                        <li>Você é responsável por manter a confidencialidade de suas credenciais.</li>
                        <li>É proibido compartilhar sua conta ou código de convite com terceiros.</li>
                        <li>Você deve ter pelo menos 18 anos para utilizar o serviço.</li>
                    </ul>
                </Section>

                <Section title="4. Uso Aceitável">
                    <p>É <strong>proibido</strong>:</p>
                    <ul>
                        <li>Usar a plataforma para gerar conteúdo ilegal, difamatório, discriminatório ou que viole direitos de terceiros.</li>
                        <li>Realizar engenharia reversa, copiar ou redistribuir o serviço.</li>
                        <li>Tentar acessar dados de outros usuários.</li>
                        <li>Usar a IA para gerar desinformação ou conteúdo enganoso.</li>
                        <li>Sobrecarregar os sistemas com requisições automatizadas excessivas.</li>
                    </ul>
                </Section>

                <Section title="5. Propriedade do Conteúdo">
                    <p>
                        O conteúdo gerado pela Logia com base nos seus dados pertence a você. Você
                        concede à Logia uma licença limitada para processar esse conteúdo com o
                        objetivo de fornecer o serviço. A Logia não usa seu conteúdo para treinar
                        modelos de IA.
                    </p>
                </Section>

                <Section title="6. Pagamentos e Cancelamento">
                    <p>
                        Durante o período de beta, o acesso é gratuito. Ao migrar para planos pagos,
                        os valores e condições serão comunicados com pelo menos 30 dias de antecedência.
                        Você pode cancelar sua conta a qualquer momento através de{" "}
                        <Link to="/settings" className="text-[#6366F1] hover:underline">Configurações → Excluir conta</Link>.
                    </p>
                </Section>

                <Section title="7. Limitação de Responsabilidade">
                    <p>
                        A Logia fornece o serviço "como está". Não garantimos disponibilidade
                        ininterrupta ou que o conteúdo gerado por IA seja sempre preciso. Em nenhum
                        caso nossa responsabilidade excederá o valor pago pelo serviço nos últimos
                        3 meses.
                    </p>
                </Section>

                <Section title="8. Privacidade">
                    <p>
                        O tratamento dos seus dados pessoais é regido pela nossa{" "}
                        <Link to="/privacy" className="text-[#6366F1] hover:underline">
                            Política de Privacidade
                        </Link>
                        , elaborada em conformidade com a Lei Geral de Proteção de Dados (LGPD —
                        Lei nº 13.709/2018).
                    </p>
                </Section>

                <Section title="9. Alterações nos Termos">
                    <p>
                        Podemos atualizar estes Termos periodicamente. Alterações materiais serão
                        comunicadas por email com pelo menos 15 dias de antecedência. O uso continuado
                        do serviço após esse prazo constitui aceitação.
                    </p>
                </Section>

                <Section title="10. Foro e Lei Aplicável">
                    <p>
                        Estes Termos são regidos pelas leis brasileiras. Fica eleito o Foro da
                        Comarca de São Paulo/SP para dirimir quaisquer controvérsias.
                    </p>
                </Section>

                <div className="border-t border-[#2E2E2E] pt-6 text-sm text-[#6B7280] space-y-1">
                    <p>{COMPANY}</p>
                    <p>
                        Dúvidas:{" "}
                        <a href={`mailto:${EMAIL}`} className="text-[#9CA3AF] hover:text-[#F9FAFB]">
                            {EMAIL}
                        </a>
                    </p>
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
