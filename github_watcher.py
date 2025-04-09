import time
from datetime import datetime, timedelta
from github import Github, RateLimitExceededException, BadCredentialsException
from logger import logger

class GitHubWatcher:
    def __init__(self, access_token=None):
        """
        Инициализация модуля для отслеживания активности репозиториев на GitHub
        
        Args:
            access_token (str, optional): Токен доступа GitHub для увеличения лимита запросов API
        """
        try:
            # Создаем клиент GitHub (с токеном или без)
            if access_token:
                self.github = Github(access_token)
                self.using_auth = True
                logger.info("GitHub API инициализирован с аутентификацией")
            else:
                self.github = Github()
                self.using_auth = False
                logger.info("GitHub API инициализирован без аутентификации (ограниченный доступ)")
            
            # Проверяем лимиты для использования API
            rate_limit = self.github.get_rate_limit()
            logger.info(f"Лимит API GitHub: {rate_limit.core.remaining}/{rate_limit.core.limit} запросов")
            
            # Список интересующих нас криптопроектов (организация/репозиторий)
            self.crypto_repos = [
                "bitcoin/bitcoin",
                "ethereum/go-ethereum",
                "solana-labs/solana",
                "cosmos/cosmos-sdk",
                "binance-chain/bsc",
                "cardano-foundation/cardano-wallet"
            ]
        except BadCredentialsException:
            logger.error("Неверный токен доступа GitHub")
            self.github = None
        except Exception as e:
            logger.error(f"Ошибка при инициализации GitHub API: {str(e)}")
            self.github = None
    
    def get_repo_activity(self, repo_path, days=7):
        """
        Получает информацию об активности в конкретном репозитории
        
        Args:
            repo_path (str): Путь к репозиторию в формате 'organization/repo'
            days (int): Количество дней для анализа активности
            
        Returns:
            dict: Информация об активности или None в случае ошибки
        """
        if not self.github:
            return None
            
        try:
            # Получаем репозиторий
            repo = self.github.get_repo(repo_path)
            
            # Базовая информация о репозитории
            repo_info = {
                "name": repo.name,
                "full_name": repo.full_name,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "watchers": repo.subscribers_count,
                "updated_at": repo.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "days_analyzed": days
            }
            
            # Рассчитываем дату, от которой считаем коммиты
            since_date = datetime.now() - timedelta(days=days)
            
            # Получаем коммиты за период
            commits = list(repo.get_commits(since=since_date))
            repo_info["commits_count"] = len(commits)
            
            # Вычисляем среднее количество коммитов в день
            if days > 0:
                repo_info["avg_commits_per_day"] = round(repo_info["commits_count"] / days, 2)
            else:
                repo_info["avg_commits_per_day"] = 0
                
            # Получаем последнюю дату коммита, если есть коммиты
            if commits:
                repo_info["last_commit_date"] = commits[0].commit.author.date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                repo_info["last_commit_date"] = "No recent commits"
                
            # Добавляем ссылку на репозиторий
            repo_info["url"] = repo.html_url
            
            logger.info(f"Успешно получена информация о репозитории {repo_path}: {repo_info['commits_count']} коммитов за последние {days} дней")
            
            # Определяем уровень активности
            if repo_info["avg_commits_per_day"] >= 10:
                repo_info["activity_level"] = "Very High"
                repo_info["activity_emoji"] = "🔥"
            elif repo_info["avg_commits_per_day"] >= 5:
                repo_info["activity_level"] = "High"
                repo_info["activity_emoji"] = "📈"
            elif repo_info["avg_commits_per_day"] >= 1:
                repo_info["activity_level"] = "Moderate"
                repo_info["activity_emoji"] = "📊"
            elif repo_info["avg_commits_per_day"] > 0:
                repo_info["activity_level"] = "Low"
                repo_info["activity_emoji"] = "📉"
            else:
                repo_info["activity_level"] = "Inactive"
                repo_info["activity_emoji"] = "💤"
                
            return repo_info
            
        except RateLimitExceededException:
            rate_limit = self.github.get_rate_limit()
            reset_time = rate_limit.core.reset.strftime("%Y-%m-%d %H:%M:%S")
            logger.error(f"Превышен лимит запросов GitHub API. Сброс в {reset_time}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении активности репозитория {repo_path}: {str(e)}")
            return None
    
    def get_all_repos_activity(self, days=7):
        """
        Получает информацию об активности для всех отслеживаемых репозиториев
        
        Args:
            days (int): Количество дней для анализа активности
            
        Returns:
            dict: Словарь с данными активности по всем репозиториям
        """
        all_activity = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "days_analyzed": days,
            "repos": []
        }
        
        total_commits = 0
        total_stars = 0
        
        # Проходим по всем репозиториям
        for repo_path in self.crypto_repos:
            # Даем небольшую паузу, чтобы не достичь лимита API
            time.sleep(1)
            
            repo_activity = self.get_repo_activity(repo_path, days)
            
            if repo_activity:
                all_activity["repos"].append(repo_activity)
                total_commits += repo_activity.get("commits_count", 0)
                total_stars += repo_activity.get("stars", 0)
        
        # Добавляем суммарную статистику
        all_activity["total_commits"] = total_commits
        all_activity["total_stars"] = total_stars
        all_activity["avg_commits_per_repo"] = round(total_commits / len(all_activity["repos"]), 2) if all_activity["repos"] else 0
        
        # Вычисляем общий уровень активности в экосистеме
        avg_commits_per_day_per_repo = all_activity["avg_commits_per_repo"] / days if days > 0 else 0
        
        if avg_commits_per_day_per_repo >= 10:
            all_activity["ecosystem_activity"] = "Very High"
            all_activity["ecosystem_emoji"] = "🔥"
        elif avg_commits_per_day_per_repo >= 5:
            all_activity["ecosystem_activity"] = "High"
            all_activity["ecosystem_emoji"] = "📈"
        elif avg_commits_per_day_per_repo >= 1:
            all_activity["ecosystem_activity"] = "Moderate"
            all_activity["ecosystem_emoji"] = "📊"
        elif avg_commits_per_day_per_repo > 0:
            all_activity["ecosystem_activity"] = "Low"
            all_activity["ecosystem_emoji"] = "📉"
        else:
            all_activity["ecosystem_activity"] = "Inactive"
            all_activity["ecosystem_emoji"] = "💤"
        
        return all_activity
    
    def format_github_message(self, github_data):
        """
        Форматирует данные активности GitHub для отображения в Telegram
        
        Args:
            github_data (dict): Данные, полученные от метода get_all_repos_activity
            
        Returns:
            str: Форматированное сообщение для Telegram
        """
        if not github_data or "repos" not in github_data or not github_data["repos"]:
            return "❌ Не удалось получить данные о GitHub активности."
        
        # Основная информация
        message = f"🔍 *GitHub Activity Pulse*\n\n"
        
        # Добавляем общую информацию об экосистеме
        ecosystem_emoji = github_data.get("ecosystem_emoji", "❓")
        ecosystem_activity = github_data.get("ecosystem_activity", "Unknown")
        days = github_data.get("days_analyzed", 7)
        
        message += f"{ecosystem_emoji} *Ecosystem Activity:* {ecosystem_activity}\n"
        message += f"📈 *Total commits (last {days} days):* {github_data.get('total_commits', 0)}\n"
        message += f"⭐ *Total stars:* {github_data.get('total_stars', 0)}\n\n"
        
        # Сортируем репозитории по количеству коммитов (по убыванию)
        sorted_repos = sorted(
            github_data["repos"], 
            key=lambda r: r.get("commits_count", 0), 
            reverse=True
        )
        
        # Добавляем информацию по каждому репозиторию
        message += "*Repository Activity:*\n"
        
        for repo in sorted_repos:
            repo_name = repo.get("full_name", "Unknown")
            commits = repo.get("commits_count", 0)
            stars = repo.get("stars", 0)
            activity_emoji = repo.get("activity_emoji", "❓")
            
            message += f"{activity_emoji} *{repo_name}*: {commits} commits, {stars} stars\n"
        
        # Добавляем временную метку
        timestamp = github_data.get("timestamp", "N/A")
        message += f"\n🕐 *Updated:* {timestamp}"
        
        return message