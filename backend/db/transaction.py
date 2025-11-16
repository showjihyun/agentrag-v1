"""
Transaction Management Utilities
트랜잭션 관리를 위한 Context Manager 및 데코레이터
"""

from contextlib import contextmanager
from functools import wraps
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


@contextmanager
def transaction(db: Session, auto_commit: bool = True):
    """
    트랜잭션 컨텍스트 매니저
    
    자동으로 commit/rollback 처리하여 트랜잭션 누락 방지
    
    Args:
        db: Database session
        auto_commit: True면 자동 commit, False면 수동 commit
        
    Example:
        with transaction(db):
            user = User(name="test")
            db.add(user)
            # commit은 자동으로 처리됨
            
        # 수동 commit
        with transaction(db, auto_commit=False) as tx:
            user = User(name="test")
            db.add(user)
            tx.commit()  # 명시적 commit
    """
    class TransactionContext:
        def __init__(self, session):
            self.session = session
            self.committed = False
            
        def commit(self):
            """명시적 commit"""
            self.session.commit()
            self.committed = True
            logger.debug("Transaction committed manually")
    
    tx = TransactionContext(db)
    
    try:
        yield tx
        
        # auto_commit이 True이고 아직 commit 안 했으면 자동 commit
        if auto_commit and not tx.committed:
            db.commit()
            logger.debug("Transaction auto-committed")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction rolled back: {e}")
        raise


def transactional(auto_commit: bool = True):
    """
    트랜잭션 데코레이터
    
    함수 실행 후 자동으로 commit/rollback 처리
    
    Args:
        auto_commit: True면 자동 commit
        
    Example:
        @transactional()
        def create_user(db: Session, name: str):
            user = User(name=name)
            db.add(user)
            return user
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # db 세션 찾기 (첫 번째 Session 타입 인자)
            db = None
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break
            
            if db is None:
                # kwargs에서 찾기
                db = kwargs.get('db')
            
            if db is None:
                # db 세션이 없으면 그냥 실행
                return func(*args, **kwargs)
            
            # 트랜잭션 컨텍스트에서 실행
            with transaction(db, auto_commit=auto_commit):
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


@contextmanager
def savepoint(db: Session, name: str = None):
    """
    Savepoint 컨텍스트 매니저
    
    중첩 트랜잭션을 위한 savepoint 생성
    
    Args:
        db: Database session
        name: Savepoint 이름 (선택)
        
    Example:
        with transaction(db):
            user = User(name="test")
            db.add(user)
            
            try:
                with savepoint(db, "before_profile"):
                    profile = Profile(user=user)
                    db.add(profile)
                    # 에러 발생 시 여기까지만 rollback
            except Exception:
                pass  # user는 유지됨
    """
    import uuid
    
    if name is None:
        name = f"sp_{uuid.uuid4().hex[:8]}"
    
    # Savepoint 생성
    db.execute(f"SAVEPOINT {name}")
    logger.debug(f"Savepoint created: {name}")
    
    try:
        yield
        # Savepoint 해제
        db.execute(f"RELEASE SAVEPOINT {name}")
        logger.debug(f"Savepoint released: {name}")
    except Exception as e:
        # Savepoint로 rollback
        db.execute(f"ROLLBACK TO SAVEPOINT {name}")
        logger.warning(f"Rolled back to savepoint: {name}")
        raise


def readonly_transaction(db: Session):
    """
    읽기 전용 트랜잭션
    
    실수로 데이터를 변경하는 것을 방지
    
    Example:
        with readonly_transaction(db):
            users = db.query(User).all()
            # commit/rollback 없음
    """
    return _readonly_context(db)


@contextmanager
def _readonly_context(db: Session):
    """읽기 전용 컨텍스트 내부 구현"""
    try:
        yield db
    finally:
        # 읽기 전용이므로 rollback만 수행
        db.rollback()
        logger.debug("Read-only transaction completed")
