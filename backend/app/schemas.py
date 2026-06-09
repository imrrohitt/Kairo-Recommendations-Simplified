from pydantic import BaseModel, ConfigDict


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    brand: str
    price: float

    model_config = ConfigDict(from_attributes=True)


class CartItemOut(BaseModel):
    id: int
    quantity: int
    product: ProductOut

    model_config = ConfigDict(from_attributes=True)


class RecommendRequest(BaseModel):
    user_id: int
    top_k: int = 10


class RecommendationOut(BaseModel):
    product: ProductOut
    score: float
    reason: str


class RecommendResponse(BaseModel):
    user_id: int
    cart: list[CartItemOut]
    recommendations: list[RecommendationOut]


class CartUpdateRequest(BaseModel):
    user_id: int
    product_id: int
    quantity: int = 1
