# FabricOpsFlow

Framework de CI/CD para automação completa de projetos no Microsoft Fabric, integrando Azure DevOps Pipelines, autenticação via Service Principal e deploy automatizado com a biblioteca [pyFabricOps](https://pypi.org/project/pyfabricops/).

![highlevel_architeture](support/highlevel_architeture.png)

## O que é

O FabricOpsFlow automatiza todo o ciclo de vida de um projeto Microsoft Fabric — desde a criação da infraestrutura (workspaces, lakehouses, pools, environments) até o deploy contínuo de artefatos (notebooks, semantic models, reports e mais) via Azure DevOps Pipelines.

## Principais Funcionalidades

- **Inicialização completa do ambiente**: Script interativo (Jupyter Notebook) que provisiona workspaces (DEV/PRD), lakehouses na arquitetura medallion (bronze, silver, gold), Spark pools, environments com bibliotecas pré-instaladas, Variable Libraries e conexão com Azure DevOps — tudo via REST API.
- **Deploy automatizado com 3 modos**:
  - `selective` — deploya apenas os itens alterados (baseado em `git diff`)
  - `specific` — deploya itens específicos informados manualmente
  - `full` — deploya todos os itens do repositório
- **Troca automática de parâmetros entre ambientes**: Substitui IDs de workspaces, lakehouses e connection strings em notebooks e semantic models ao promover de DEV para PRD.
- **Conversão automática de relatórios**: Converte definições de reports antes do deploy para garantir compatibilidade com o workspace de destino.
- **Autenticação segura**: Credenciais armazenadas no Azure Key Vault e injetadas via Variable Groups no Azure DevOps.
- **Gestão de permissões**: Atribuição automática de roles (Admin/Owner) a usuários e service principals nos workspaces e conexões.

## Arquitetura

| Componente | Descrição |
|---|---|
| `support/init_fabricopsflow.ipynb` | Notebook de inicialização que provisiona toda a infraestrutura |
| `azure_pipelines/deploy.yml` | Pipeline do Azure DevOps para CI/CD |
| `scripts/deploy.py` | Script de deploy que orquestra a publicação de itens no workspace |
| `scripts/utils.py` | Utilitários Git para detecção de itens alterados |
| `src/` | Diretório com os artefatos do Fabric versionados (notebooks, semantic models, reports, etc.) |

## Fluxo de Trabalho

1. **Desenvolvedores** trabalham nos workspaces feature **FEAT**, conectados às branches `feature/etc`
2. **Pull requests**, assim que aprovados e mergeados com a branch `develop` disparam o deploy para os workspaces de **DEV**
3. Assim que as features atingem um novo entregável, **Pull requests** para a branch `main` disparam o deploy para os workspaces de **PRD**
4. O pipeline **detecta os itens alterados**, realiza a **troca de parâmetros** entre ambientes e **deploya** no workspace correspondente
5. **Reports** passam por conversão de definição antes do deploy 

## Pré-requisitos

- Microsoft Entra: App Registration com permissões para Power BI, Azure DevOps e Key Vault
- Azure Key Vault com as credenciais do Service Principal
- Azure DevOps: Organização, projeto e repositório configurados
- Microsoft Fabric: Permissões de API habilitadas para o grupo do Service Principal

Consulte o [notebook de inicialização](support/init_fabricopsflow.ipynb) para instruções detalhadas.

## Tecnologias

- **Microsoft Fabric** (Workspaces, Lakehouses, Notebooks, Semantic Models, Reports, Variable Libraries, Spark Pools & Environments)
- **Azure DevOps Pipelines** (CI/CD)
- **Azure Key Vault** (Gestão de segredos)
- **Microsoft Entra / Service Principal** (Autenticação)
- **Python** + [pyFabricOps](https://pypi.org/project/pyfabricops/) (SDK)

## Licença

[MIT](LICENSE) © 2026 Alison Pezzott